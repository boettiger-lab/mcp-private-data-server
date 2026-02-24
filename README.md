# Private MCP DuckDB Geospatial Data Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing authenticated SQL query access to private geospatial datasets stored in S3. Built with DuckDB for high-performance analytics on H3-indexed environmental and land data.

**Endpoint:** `https://private-duckdb-mcp.nrp-nautilus.io/mcp`
**Hosted on:** [NRP Nautilus](https://nautilus.optiputer.net) Kubernetes cluster — namespace `biodiversity`, deployment `duckdb-mcp-private`

> **Authentication required.** Every request must include a Bearer token. See [Authentication](#authentication) below.

---

## Authentication

All requests to this server require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

Requests without a valid token receive a `401 Unauthorized` response. CORS preflight (`OPTIONS`) requests are exempt so that browser-based clients work correctly.

### Retrieving the token

The token is stored as a Kubernetes secret in the `biodiversity` namespace:

```bash
kubectl get secret mcp-private-secrets -n biodiversity \
  -o jsonpath='{.data.mcp-auth-token}' | base64 -d
```

---

## Client Configuration

### Claude Code (CLI)

Add a `.mcp.json` file to your project root (this file is gitignored in this repo — never commit it):

```json
{
  "mcpServers": {
    "private-duckdb": {
      "type": "http",
      "url": "https://private-duckdb-mcp.nrp-nautilus.io/mcp",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "private-duckdb": {
      "type": "http",
      "url": "https://private-duckdb-mcp.nrp-nautilus.io/mcp",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

### VSCode

Create `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "private-duckdb": {
      "type": "http",
      "url": "https://private-duckdb-mcp.nrp-nautilus.io/mcp",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

> **Security note:** Do not commit configuration files that contain the token. Add them to `.gitignore`.

---

## Available Datasets

See [datasets.md](datasets.md) for full schema documentation. This file is embedded directly into the MCP tool description so the LLM uses it to guide query construction.

1. **GYE Parcels** — Greater Yellowstone Ecosystem land parcels with easements, USDA program enrollment, and wildlife overlap (elk, mule deer, pronghorn crucial winter habitat). Stored at `s3://private-wyoming/gye-parcels/`.

---

## Architecture

### S3 Credential Routing

The server manages two separate S3 credential sets, applied per-query using DuckDB's secrets manager:

| Secret name | Endpoint | Scope | Source |
|---|---|---|---|
| `nrp_s3` | `rook-ceph-rgw-nautiluss3.rook` (internal NRP) | all `s3://` paths | `mcp-private-secrets` k8s Secret |
| `wyoming_s3` | `minio.carlboettiger.info` | `s3://private-wyoming` only | `mcp-private-wyoming-secrets` k8s Secret |

DuckDB's `SCOPE` parameter ensures requests to `s3://private-wyoming/**` automatically route to the MinIO endpoint with the correct credentials, while all other S3 paths use the NRP Ceph endpoint.

### Core Components

- **`server.py`** — MCP server with `BearerTokenAuth` middleware and dual S3 secret injection
- **`datasets.md`** — Dataset catalog injected into the LLM tool description
- **`query-setup.md`** — DuckDB setup SQL (extensions, thread count, base S3 config)
- **`query-optimization.md`** — Performance guidelines injected into tool description
- **`h3-guide.md`** — H3 spatial indexing reference injected into tool description
- **`k8s/`** — Kubernetes deployment manifests

### Key Design Patterns

1. **Bearer token auth**: Pure ASGI middleware wraps the MCP app at startup; checks every non-OPTIONS HTTP request
2. **Dual scoped secrets**: Per-query DuckDB `CREATE OR REPLACE SECRET` with `SCOPE` for bucket-level routing
3. **Prompt engineering**: SQL rules, dataset catalog, and spatial guides are injected into the tool description so the LLM always has context
4. **Query isolation**: Each query gets a fresh in-memory DuckDB connection — no state leaks between requests

---

## Kubernetes Deployment

### Prerequisites

Two k8s Secrets must exist in the `biodiversity` namespace before deploying.

**`mcp-private-secrets`** — MCP auth token and NRP S3 credentials:

```bash
kubectl create secret generic mcp-private-secrets \
  --from-literal=aws-access-key-id=<nrp-key-id> \
  --from-literal=aws-secret-access-key=<nrp-secret> \
  --from-literal=mcp-auth-token=<bearer-token> \
  -n biodiversity
```

To generate a strong bearer token: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

**`mcp-private-wyoming-secrets`** — MinIO credentials for `private-wyoming` bucket:

```bash
kubectl create secret generic mcp-private-wyoming-secrets \
  --from-literal=wyoming-s3-key-id=<minio-key-id> \
  --from-literal=wyoming-s3-secret=<minio-secret> \
  -n biodiversity
```

See [`k8s/secret-template.yaml`](k8s/secret-template.yaml) for the Secret manifest format.

### Deploy

```bash
kubectl apply -f k8s/deployment.yaml -n biodiversity
kubectl apply -f k8s/service.yaml -n biodiversity
kubectl apply -f k8s/ingress.yaml -n biodiversity
```

### Update credentials

To update a secret without recreating it (preserves other keys):

```bash
kubectl create secret generic mcp-private-secrets \
  --from-literal=aws-access-key-id=<new-key> \
  --from-literal=aws-secret-access-key=<new-secret> \
  --from-literal=mcp-auth-token=<token> \
  --dry-run=client -o yaml | kubectl apply -f - -n biodiversity

kubectl rollout restart deployment/duckdb-mcp-private -n biodiversity
```

### Adding a new dataset

1. Add data to S3 (NRP Ceph or MinIO as appropriate)
2. If using a new S3 endpoint/bucket with credentials, add a new k8s Secret and wire it into `k8s/deployment.yaml` as env vars
3. Add a scoped `CREATE OR REPLACE SECRET` in `get_isolated_db()` in `server.py`
4. Document the dataset in `datasets.md` (schema, S3 path, join keys)
5. Push and restart: `kubectl rollout restart deployment/duckdb-mcp-private -n biodiversity`

---

## MinIO User Management

The `wyoming-app` service account on `minio.carlboettiger.info` has read/write access scoped to `private-wyoming` only. To manage it:

```bash
# List access keys
mc admin accesskey list nvme wyoming-app

# View current policy
mc admin policy info nvme wyoming-app-policy

# Update policy
mc admin policy create nvme wyoming-app-policy policy.json
mc admin policy detach nvme wyoming-app-policy --user wyoming-app
mc admin policy attach nvme wyoming-app-policy --user wyoming-app
```

Note: When using `rclone` to write to this bucket, add `--s3-no-check-bucket` to prevent rclone from attempting to `PUT` (create) the bucket — which would fail because the service account does not have `s3:CreateBucket` permission.

---

## MCP Protocol Features

### Tools
- `query(sql_query)` — Execute DuckDB SQL with embedded optimization rules and dataset catalog

### Resources
- `catalog://list` — List all available datasets
- `catalog://{name}` — Get detailed schema for a specific dataset

### Prompts
- `geospatial-analyst` — Load complete geospatial analysis persona

> Note: Resources and Prompts are only visible in clients that support them (Claude Code, Continue.dev). VSCode's Copilot MCP integration currently only exposes Tools.

---

## Security Model

| Layer | Mechanism |
|---|---|
| Request auth | Bearer token (`MCP_AUTH_TOKEN` env var), checked on every non-OPTIONS request |
| S3 data access | Scoped per-bucket credentials from k8s Secrets, never exposed to callers |
| Query isolation | Fresh in-memory DuckDB per request — no shared state |
| Code secrecy | Repo is public; all secrets live exclusively in k8s Secrets |
| Token storage | k8s Secret `mcp-private-secrets`, key `mcp-auth-token` |

---

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DuckDB Secrets Manager](https://duckdb.org/docs/sql/statements/create_secret.html)
- [H3 Geospatial Indexing](https://h3geo.org)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
