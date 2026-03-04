# Available Datasets (Private)

**IMPORTANT** You must read remote parquet datasets with read_parquet()

---

**1. GYE Parcels (Wyoming Private)**
- Flat parquet: `s3://private-wyoming/gye-parcels/gye-parcels.parquet`
- H3-indexed parquet: `s3://private-wyoming/gye-parcels/hex/**` (partitioned by `h0`)
- **5,170 parcels** across 7 Wyoming counties in the Greater Yellowstone Ecosystem
- H3 resolutions available: `h9`, `h10`, `h11` (and `h0` partition column)

**IMPORTANT: This dataset has TWO distinct types of wildlife habitat columns. Do NOT confuse them:**
1. **Crucial Winter Range** columns contain `crucialwinter` in the name — these describe where animals spend winter, NOT where they migrate.
2. **Migration Corridor** columns contain `medium_use` or `high_use` in the name — these describe the paths animals travel between seasonal ranges.
If a user asks about migration corridors, use the migration corridor columns. If they ask about winter range or winter habitat, use the crucialwinter columns.

---

## General Parcel Description

- `uid` (INTEGER) — Unique parcel identifier, used to join to other layers (e.g., social willingness layer from JHLT)
- `parcelnb` (VARCHAR) — Parcel number
- `county` (VARCHAR) — County where the majority of the parcel occurs
- `state` (VARCHAR) — State (always 'WY')
- `parcel_class` (VARCHAR) — Land use classification from county assessor data (2024): 'Residential', 'Agricultural', or NA
- `area_acres` (DOUBLE) — Area of the parcel in acres. Note: parcels do not have to be contiguous to share a parcel number
- `actual_value` (DOUBLE) — Assessed parcel value in US dollars, from tax assessor data (2023)
- `actual_value_peracre` (DOUBLE) — Parcel value in US dollars per acre (actual_value / area_acres)
- `ownername` (VARCHAR) — Owner name
- `address` (VARCHAR) — Owner address
- `taxyear` (VARCHAR) — Tax assessment year

## Easement and Conservation

- `percent_easement` (DOUBLE) — Percent of the parcel under conservation easement
- `percent_perim_easement` (DOUBLE) — Percent of the parcel perimeter that touches or is within 25 m (82 ft) of an existing conservation easement

## Administrative and Protected Area Designations

- `percent_gsg_corearea` (DOUBLE) — Percent of the parcel within Greater Sage Grouse Core Areas (WY Game and Fish Dept data)
- `in_usda_pa` (DOUBLE) — Binary (1/0): whether the parcel is in or touches a Wyoming USDA-NRCS Priority Area
- `percent_scd_core` (DOUBLE) — Percent of the parcel within Core Sagebrush Areas (Sagebrush Conservation Design)
- `percent_scd_growth` (DOUBLE) — Percent of the parcel within sagebrush Growth Opportunity Areas (Sagebrush Conservation Design)
- `percent_usda_primefarm` (DOUBLE) — Percent of the parcel within USDA Prime Farmland (soils that economically produce high crop yields)
- `percent_usda_farm_state_important` (DOUBLE) — Percent of the parcel within USDA Farmland of Statewide Importance
- `in_nrcs_gcrp_priorityzone` (DOUBLE) — Binary (1/0): whether the parcel is in or touches the Grassland CRP Greater Yellowstone Wildlife Corridor Priority Zone (Lincoln, Park, Sublette, Teton, Fremont, or Hot Springs counties)
- `percent_gcrp` (DOUBLE) — Percent of the parcel enrolled in Grassland Conservation Reserve Program (typically close to 100 for enrolled parcels)
- `year_expire_gcrp` (DOUBLE) — If >=5% of parcel is enrolled in Grassland CRP, the year the contract expires
- `n_equip` (DOUBLE) — Number of USDA NRCS Environmental Quality Incentives Program (EQIP) contracts within the parcel
- `year_last_equip` (DOUBLE) — If n_equip > 0, the most recent year of the EQIP contract(s)
- `fence_equip` (DOUBLE) — Binary (1/0): if n_equip > 0, whether any contracts relate to fence conversion/modification (includes NRCS practices: "fences", "structures for wildlife", "obstruction removal")

## Big Game Crucial Winter Range

These columns describe overlap with **crucial winter range** — the areas where elk, mule deer, and pronghorn spend winter. This includes crucial winter range/year-round and severe winter relief areas. **These are NOT migration corridors.** Species: `elk`, `muledeer`, `pronghorn`.

- `percent_overlap_{species}_crucialwinter` (DOUBLE) — Percent of the parcel's area that overlaps with WY Game and Fish crucial winter range for that species
- `percent_overall_{species}_crucialwinter` (DOUBLE) — If parcel is on crucial winter range, the percent of the entire herd's crucial winter range area that this parcel represents
- `percent_protected_{species}_crucialwinter` (DOUBLE) — If parcel is on crucial winter range, percent of protected land (public lands + conservation easements) within the herd's crucial winter range that this parcel represents
- `percent_unprotected_{species}_crucialwinter` (DOUBLE) — If parcel is on crucial winter range, percent of unprotected private land within the herd's crucial winter range that this parcel represents. A value of 30% means this parcel's area is 30% of all unprotected private land in the crucial winter range
- `area_within_acres_{species}_crucialwinter` (DOUBLE) — Acres of the parcel within crucial winter range
- `area_neighbor_{species}_crucialwinter` (DOUBLE) — Neighboring acres in crucial winter range (within 25 m buffer)
- `area_contiguous_acres_{species}_crucialwinter` (DOUBLE) — Contiguous area of this parcel AND all neighboring public lands AND neighboring private lands under conservation easement within crucial winter range
- `area_protected_acres_{species}_crucialwinter` (DOUBLE) — Protected acres within the crucial winter range
- `area_unprotected_acres_{species}_crucialwinter` (DOUBLE) — Unprotected acres within the crucial winter range

## Big Game Migration Corridors and Crossings

These columns describe overlap with **migration corridors** — the paths animals travel between seasonal ranges. Corridors are classified as **medium use** or **high use** based on the number of animals using them. Species: `elk`, `muledeer`, `pronghorn`. **These are NOT winter range.**

### Individual Animal Migration Counts

- `n_aid_pronghorn` (DOUBLE) — Number of unique individual pronghorn that migrate across or within 300 m (0.19 miles) of the parcel. The 300 m buffer represents the width of space necessary for functional migration.
- `n_aid_elk` (DOUBLE) — Number of unique individual elk that migrate across or within 300 m of the parcel
- `n_aid_muledeer` (DOUBLE) — Number of unique individual mule deer that migrate across or within 300 m of the parcel
- `n_aid_allsp` (DOUBLE) — Total number of unique individual animals (all three species combined) that migrate across or within 300 m of the parcel

### Herd Migration Percentages

- `percent_herd_pronghorn` (DOUBLE) — Percent of the pronghorn herd (defined by WY Game and Fish herd units) that migrates through the parcel (using 300 m buffer around individual migration lines)
- `percent_herd_elk` (DOUBLE) — Percent of the elk herd that migrates through the parcel
- `percent_herd_muledeer` (DOUBLE) — Percent of the mule deer herd that migrates through the parcel
- `percent_herd_allsp` (DOUBLE) — Combined migration percentage across all three species: (percent_herd_pronghorn + percent_herd_elk + percent_herd_muledeer) / 300, scaled to 0-100

### Bottlenecks and Stopovers

- `in_wgfd_bottleneck` (DOUBLE) — Binary (1/0): whether the parcel is in or touches a WY Game and Fish designated migration bottleneck
- `percent_wgfd_muledeerstop` (DOUBLE) — Percent of the parcel that overlaps WY Game and Fish designated mule deer stopover areas. **NOTE: this column may not yet be available in the dataset.**

### Migration Corridor Width

These measure how much of the corridor's cross-sectional width a parcel occupies. The width is the shortest distance from one side of the corridor to the other at the parcel's centroid. Use pattern: `percent_corridor_width_{species}_{use_level}` and `percent_corridor_width_unprotected_{species}_{use_level}`. Species: `pronghorn`, `elk`, `muledeer`. Use levels: `medium_use`, `high_use`.

- `percent_corridor_width_{species}_{use_level}` (DOUBLE) — If parcel is on or touches the corridor, percent of the corridor's width that this parcel occupies
- `percent_corridor_width_unprotected_{species}_{use_level}` (DOUBLE) — If parcel is on the corridor, percent of the corridor's width that remains unprotected if this parcel becomes protected

### Migration Corridor Area and Protection Status

These measure the parcel's area relative to the total corridor area. Use pattern: `percent_overall_{species}_{use_level}`, `percent_protected_{species}_{use_level}`, `percent_unprotected_{species}_{use_level}`. Species: `pronghorn`, `elk`, `muledeer`. Use levels: `medium_use`, `high_use`.

- `percent_overall_{species}_{use_level}` (DOUBLE) — Percent of the entire corridor's area that this parcel within the corridor represents
- `percent_protected_{species}_{use_level}` (DOUBLE) — Percent of all protected land (public + easements) within the corridor that this parcel represents. A value of 10% means this parcel occupies 10% of all already-protected land in the corridor
- `percent_unprotected_{species}_{use_level}` (DOUBLE) — Percent of all unprotected land (private without easement + reservation lands) within the corridor that this parcel represents. A value of 20% means this parcel occupies 20% of all unprotected land in the corridor

### Migration Corridor Area Metrics

All use the pattern `{metric}_{species}_{use_level}`. Species: `elk`, `muledeer`, `pronghorn`. Use levels: `medium_use`, `high_use`.

- `area_within_acres_{species}_{use_level}` (DOUBLE) — Acres of the parcel within the migration corridor
- `area_neighbor_{species}_{use_level}` (DOUBLE) — Neighboring acres in the migration corridor (within 25 m buffer)
- `area_contiguous_acres_{species}_{use_level}` (DOUBLE) — Area of the parcel within the migration corridor plus adjacent contiguous protected lands (public land and private land under conservation easement)
- `area_protected_acres_{species}_{use_level}` (DOUBLE) — Protected acres within the migration corridor
- `area_unprotected_acres_{species}_{use_level}` (DOUBLE) — Unprotected acres within the migration corridor

## Fences

Based on an AI model predicting fences in open rangelands (unpublished data from Wenjing Xu / Microsoft, shared by Jerod Merkle).

- `density_fences_total` (DOUBLE) — Density of fence in miles per square mile. Calculated as interior fences + one half of exterior fences (to avoid double-counting shared boundary fences), divided by parcel area
- `length_fences_interior_mi` (DOUBLE) — Miles of interior fence within the parcel (excludes fences on the parcel boundary)
- `length_fences_total_mi` (DOUBLE) — Total miles of fence associated with the parcel: interior fences + one half of exterior fences

## Public Lands Perimeter

These measure what percent of the parcel's perimeter touches or is within 25 m (82 ft) of various public land types. The 25 m buffer accounts for small gaps between parcels.

- `percent_publicperim_allpublic` (DOUBLE) — Percent of perimeter touching any public land (excluding reservation lands). This is the sum of the individual public land type columns below, excluding Wind River Indian Reservation
- `percent_publicperim_blm` (DOUBLE) — Percent of perimeter touching Bureau of Land Management land
- `percent_publicperim_state` (DOUBLE) — Percent of perimeter touching State land
- `percent_publicperim_usfs` (DOUBLE) — Percent of perimeter touching U.S. Forest Service land
- `percent_publicperim_usfws` (DOUBLE) — Percent of perimeter touching U.S. Fish and Wildlife Service land
- `percent_publicperim_other_public` (DOUBLE) — Percent of perimeter touching other public lands
- `percent_publicperim_wrir` (DOUBLE) — Percent of perimeter touching Wind River Indian Reservation land

## Development and Impervious Surface

- `percent_impervious` (DOUBLE) — Percent of the parcel classified as impervious surface (pavement, concrete, rooftops, constructed materials) based on National Land Cover Database
- `area_acres_impervious` (DOUBLE) — Acres of the parcel classified as impervious surface
- `highway_present` (DOUBLE) — Binary (1/0): whether a highway goes through the parcel (WY Dept of Transportation data)
- `risk_development` (DOUBLE) — Predicted risk of development from TNC's model, ranging 0-1. Relative probability that the parcel could be classified as residential given its characteristics

## Vegetation and Landcover

### Cheatgrass Invasion (Rangeland Analysis Platform, 2024, 10m resolution)

- `percent_cheatgrass_high` (DOUBLE) — Percent of the parcel highly invaded by cheatgrass (>=15% cover)
- `area_cheatgrass_high_acres` (DOUBLE) — Acres of the parcel highly invaded by cheatgrass (>=15% cover)
- `percent_cheatgrass_moderate` (DOUBLE) — Percent of the parcel moderately invaded by cheatgrass (>=8% cover)
- `area_cheatgrass_moderate_acres` (DOUBLE) — Acres of the parcel moderately invaded by cheatgrass (>=8% cover)

### Irrigation and Land Cover (2019 National Land Cover Database)

- `percent_irrigated` (DOUBLE) — Percent of the parcel classified as irrigated land (Wyoming Statewide Basin Plan, 2007)
- `percent_nlcd_deciduous_forest` (DOUBLE) — Percent classified as deciduous forest (NLCD code 41)
- `percent_nlcd_evergreen_forest` (DOUBLE) — Percent classified as evergreen forest (NLCD code 42)
- `percent_nlcd_mixed_forest` (DOUBLE) — Percent classified as mixed forest (NLCD code 43)
- `percent_nlcd_pasture_hay` (DOUBLE) — Percent classified as pasture/hay (NLCD code 81)
- `percent_nlcd_cultivated_crops` (DOUBLE) — Percent classified as cultivated crops (NLCD code 82)
- `percent_nlcd_woody_wetlands` (DOUBLE) — Percent classified as woody wetlands (NLCD code 90)
- `percent_nlcd_herb_wetlands` (DOUBLE) — Percent classified as herbaceous wetlands (NLCD code 95)

## Social / Willingness (Not Yet Available)

- `prob_entering_easement` — Estimated probability of entering a conservation easement based on Jackson Hole Land Trust field knowledge. Categories: low, medium, high, unknown. **This column is not yet available in the dataset.**

## Query Guidance for the LLM

### BEFORE writing SQL, check these rules:

**1. Disambiguate winter range vs migration corridors:**
- If the user says "migration corridor", "migration path", "migration route" → use columns with `medium_use` or `high_use` (e.g., `percent_corridor_width_{species}_{use_level}`, `percent_herd_{species}`, `n_aid_{species}`)
- If the user says "winter range", "winter habitat", "crucial winter" → use columns with `crucialwinter` (e.g., `percent_overlap_{species}_crucialwinter`)
- NEVER use crucialwinter columns when the user asks about migration corridors, and vice versa

**2. Ask for species clarification when not specified:**
- If the user doesn't specify a species, ask: "Which species are you interested in — elk, mule deer, pronghorn, or all three?"
- If the user says "corridor" without specifying use level, ask: "Do you want high-use corridors, medium-use corridors, or both?"

**3. Inform users about unavailable data:**
- `prob_entering_easement` (landowner willingness/social scores) is NOT YET AVAILABLE. If asked about willingness, probability of entering easements, or social scores, inform the user this data is pending from Jackson Hole Land Trust.
- There are NO cost models in the dataset. `actual_value` is assessed tax value, NOT easement/lease/treatment cost. If asked about costs, report assessed values as a proxy and note the limitation.
- There is NO leasing data. If asked about lease vs easement optimization, explain this requires external economic modeling.
- `percent_wgfd_muledeerstop` (mule deer stopovers) may not yet be available.

**4. Note when a query needs external data or assumptions:**
- Cheatgrass treatment costs, fence modification costs, easement acquisition costs → ask the user for per-acre or per-mile rates
- "Optimal" or "best" rankings → ask the user what criteria/weights to use
- Spatial clustering or geographic adjacency beyond the contiguous area columns → explain the flat parcel data cannot compute arbitrary spatial clusters

**5. Always use COALESCE for nullable columns:**
- Most numeric columns can be NULL. Always wrap in COALESCE(column, 0) before comparisons.
