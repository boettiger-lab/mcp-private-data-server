# Available Datasets (Private)

**IMPORTANT** You must read remote parquet datasets with read_parquet()

---

**1. GYE Parcels (Wyoming Private)**
- Flat parquet: `s3://private-wyoming/gye-parcels/gye-parcels.parquet`
- H3-indexed parquet: `s3://private-wyoming/gye-parcels/hex/**` (partitioned by `h0`)
- **5,170 parcels** across 7 Wyoming counties in the Greater Yellowstone Ecosystem
- H3 resolutions available: `h9`, `h10`, `h11` (and `h0` partition column)

**Key columns:**
- `uid` (INTEGER) — unique parcel identifier
- `parcelnb` (VARCHAR) — parcel number
- `county`, `state` (VARCHAR) — e.g. 'TETON', 'WY'
- `parcel_class` (VARCHAR) — land use classification
- `area_acres` (DOUBLE) — parcel area in acres
- `actual_value`, `actual_value_peracre` (DOUBLE) — assessed value
- `ownername`, `address` (VARCHAR) — owner info
- `taxyear` (VARCHAR) — tax assessment year

**Easement / conservation columns:**
- `percent_easement`, `percent_perim_easement` (DOUBLE)
- `in_usda_pa`, `percent_usda_farm_state_important`, `percent_usda_primefarm` (DOUBLE)
- `percent_gsg_corearea`, `percent_scd_core`, `percent_scd_growth` (DOUBLE)
- `percent_gcrp`, `year_expire_gcrp`, `in_nrcs_gcrp_priorityzone` (DOUBLE)
- `n_equip`, `year_last_equip`, `fence_equip` (DOUBLE)

**Wildlife overlap columns (elk, mule deer, pronghorn — crucial winter habitat):**
- `percent_overlap_{species}_crucialwinter` — % of parcel overlapping crucial winter range
- `percent_overall_{species}_crucialwinter` — overall overlap score
- `percent_protected_{species}_crucialwinter` — overlap already under protection
- `percent_unprotected_{species}_crucialwinter` — unprotected overlap (conservation opportunity)
- `area_within_acres_{species}_crucialwinter` — acres within crucial winter range
- `area_neighbor_{species}_crucialwinter` — neighboring acres in crucial winter range
- `area_contiguous_acres_{species}_crucialwinter` — contiguous acres in crucial winter range
- `area_protected_acres_{species}_crucialwinter`, `area_unprotected_acres_{species}_crucialwinter`
- Species: `elk`, `muledeer`, `pronghorn`
