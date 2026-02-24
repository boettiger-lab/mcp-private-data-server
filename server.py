import os
import re
import duckdb
import uvicorn
import sys
from contextlib import contextmanager
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# -------------------------------------------------------------------------
# 1. INITIALIZATION
# -------------------------------------------------------------------------
mcp = FastMCP(
    "DuckDB-S3-Geo-Isolated",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

# -------------------------------------------------------------------------
# 2. CONFIGURATION & FILE LOADING
# -------------------------------------------------------------------------
def load_text_file(filename):
    paths = [
        filename,
        os.path.join("/app", filename),
        os.path.join(os.path.dirname(__file__), filename)
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, 'r') as f: return f.read()
    print(f"⚠️ Warning: Could not find {filename}", file=sys.stderr)
    return ""

def parse_setup_sql(content):
    match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    return match.group(1).strip() if match else ""

SETUP_RAW = load_text_file("query-setup.md")
SETUP_SQL = parse_setup_sql(SETUP_RAW)
CATALOG_RAW = load_text_file("datasets.md")
OPTIM_RAW = load_text_file("query-optimization.md")
H3_RAW = load_text_file("h3-guide.md")
ROLE_RAW = load_text_file("assistant-role.md")

# S3 credentials injected from environment (set via Kubernetes Secret)
S3_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
S3_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# -------------------------------------------------------------------------
# 3. CONTEXT INJECTION (PROMPT ENGINEERING)
# -------------------------------------------------------------------------
# We frame this as a "Strict Syntax Guide" rather than just "Context".
# This forces the model to abandon its training on standard "SELECT * FROM table".
TOOL_INJECTED_CONTEXT = f"""
---
### ⚠️ CRITICAL SQL RULES (MUST FOLLOW)
1. **NO TABLES EXIST:** The database is empty. You CANNOT write `FROM table_name`.
2. **USE PARQUET PATHS:** You MUST use `FROM read_parquet('s3://...')` for ALL queries.
3. **COPY PATHS EXACTLY:** Use the S3 paths listed in the Catalog below.

### 📂 DATA CATALOG (Source of Truth)
{CATALOG_RAW}

### ⚡ OPTIMIZATION RULES
{OPTIM_RAW}

### 📐 H3 SPATIAL MATH
{H3_RAW}
---
"""

# -------------------------------------------------------------------------
# 4. ISOLATION ENGINE
# -------------------------------------------------------------------------
@contextmanager
def get_isolated_db():
    conn = duckdb.connect(database=":memory:")
    try:
        if SETUP_SQL: conn.sql(SETUP_SQL)
        # Always override S3 credentials from environment variables.
        # Runs after SETUP_SQL so env vars are the unconditional source of truth.
        # Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in the k8s Secret.
        key_id = S3_KEY_ID.replace("'", "''")
        secret = S3_SECRET_KEY.replace("'", "''")
        conn.sql(
            f"CREATE OR REPLACE SECRET s3 (TYPE S3, "
            f"ENDPOINT 'rook-ceph-rgw-nautiluss3.rook', "
            f"URL_STYLE 'path', USE_SSL 'false', "
            f"KEY_ID '{key_id}', SECRET '{secret}');"
        )
        yield conn
    finally:
        conn.close()

# -------------------------------------------------------------------------
# 5. MCP RESOURCES (Schema Browsing for Smart Clients)
# -------------------------------------------------------------------------
DATA_CATALOG = {}
if CATALOG_RAW:
    sections = re.split(r'(\*\*\d+\..*?\*\*)', CATALOG_RAW)
    DATA_CATALOG["_intro"] = sections[0].strip() if sections else ""
    for i in range(1, len(sections), 2):
        header = sections[i]
        body = sections[i+1]
        clean_key = re.sub(r'[\*\d\.]', '', header).strip().lower().split('(')[0].strip().replace(' ', '_')
        DATA_CATALOG[clean_key] = header + "\n" + body.strip()

@mcp.resource("catalog://list")
def list_datasets() -> str:
    return CATALOG_RAW

@mcp.resource("catalog://{name}")
def get_dataset_details(name: str) -> str:
    if name in DATA_CATALOG: return DATA_CATALOG[name]
    for key, val in DATA_CATALOG.items():
        if name in key: return val
    return "Dataset not found."

# -------------------------------------------------------------------------
# 6. MCP PROMPTS (Personas for Smart Clients)
# -------------------------------------------------------------------------
@mcp.prompt("geospatial-analyst")
def analyst_persona() -> str:
    return f"""
    {ROLE_RAW}
    DATASETS:
    {CATALOG_RAW}
    RULES:
    {OPTIM_RAW}
    """

# -------------------------------------------------------------------------
# 7. TOOL DEFINITION & MANUAL REGISTRATION
# -------------------------------------------------------------------------
def query(sql_query: str) -> str:
    """Placeholder (overwritten below)."""
    print(f"🔍 Executing: {sql_query}", file=sys.stderr)
    try:
        with get_isolated_db() as db:
            result = db.sql(sql_query)
            if result is None: return "Command executed successfully."

            df = result.limit(50).df()
            if df.empty: return "No results found."
            return df.to_markdown(index=False)

    except Exception as e:
        return f"SQL Error: {str(e)}"

# 💉 INJECTION: Force the strict rules into the tool description
query.__doc__ = f"""
Executes optimized DuckDB SQL.
STRICTLY FOLLOW THE RULES BELOW.

{TOOL_INJECTED_CONTEXT}
"""

# ®️ REGISTER: Manually register the tool with the injected prompt
mcp.tool()(query)

# -------------------------------------------------------------------------
# 8. AUTHENTICATION MIDDLEWARE
# -------------------------------------------------------------------------
class BearerTokenAuth:
    """
    ASGI middleware that requires a valid Bearer token on every HTTP request.
    Token is read from the MCP_AUTH_TOKEN environment variable.
    CORS preflight (OPTIONS) requests are passed through unauthenticated so
    that the HAProxy ingress CORS handling continues to work correctly.
    """
    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            method = scope.get("method", "")
            # Pass OPTIONS through for CORS preflight
            if method != "OPTIONS":
                headers = dict(scope.get("headers", []))
                auth = headers.get(b"authorization", b"").decode()
                if not (auth.startswith("Bearer ") and auth[7:] == self.token):
                    await send({
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"www-authenticate", b'Bearer realm="MCP"'),
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b'{"error":"Unauthorized"}',
                        "more_body": False,
                    })
                    return
        await self.app(scope, receive, send)

# -------------------------------------------------------------------------
# 9. SERVER START
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = mcp.streamable_http_app()
    app.router.redirect_slashes = False

    auth_token = os.environ.get("MCP_AUTH_TOKEN", "")
    if auth_token:
        app = BearerTokenAuth(app, auth_token)
        print("🔒 Bearer token authentication enabled.", file=sys.stderr)
    else:
        print("⚠️  WARNING: MCP_AUTH_TOKEN not set — server is UNPROTECTED!", file=sys.stderr)

    print("🚀 Starting DuckDB MCP Server (Private)...", file=sys.stderr)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
