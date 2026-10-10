# hk-buildings

Every building in Hong Kong (about 342,000 footprints) with its own height, from the Lands Department's CSDI Building layer,
baked weekly and published for browsers and data tools to read in place.

Part of [AlreadyOpen](https://github.com/AlreadyOpen): open, re-runnable pipelines over public data.

| Output | Where | Format |
|---|---|---|
| Vector tiles for maps, z13-16 (MapLibre overzooms past 16), layer `buildings` | [huggingface.co/buckets/alreadyopen/hk-buildings](https://huggingface.co/buckets/alreadyopen/hk-buildings) `buildings.pmtiles` | PMTiles, tiles gzipped inside |
| Every building with its footprint, for queries and low zooms | [huggingface.co/datasets/alreadyopen/hk-buildings](https://huggingface.co/datasets/alreadyopen/hk-buildings) `buildings.parquet` | GeoParquet (WKB, EPSG:4326), ZSTD |

Both answer CORS and HTTP Range requests: MapLibre reads the PMTiles with the `pmtiles://` protocol, DuckDB (also DuckDB-Wasm)
reads the Parquet without downloading it whole.

## Fields

| Field | Meaning |
|---|---|
| `BuildingCSUID` | Lands Department building id |
| `BuildingNameEN`, `BuildingNameTC` | names, where the building has one |
| `BaseHeight`, `TopHeight` | metres above Hong Kong Principal Datum (mPD), not above ground |
| `height_m` | the building's own height, `TopHeight - BaseHeight` (extrude this from the ground); empty when either is missing (about 1.5k buildings) |
| `Storeys`, `StoreysInBasement`, `BuildingBlockType`, `Status` | as published by Lands D |

## Run it

```bash
pip install -r requirements.txt   # and tippecanoe 2.79.0 on PATH (github.com/felt/tippecanoe)
python buildings.py               # ~13 min: pages all buildings from CSDI -> data/out/
python publish.py                 # -> Hugging Face (needs HF_TOKEN)
```

`HKB_DATA` moves the data folder. The GitHub Action `.github/workflows/bake.yml` runs both weekly, building tippecanoe from its
tagged source once and caching it.

## Source and terms

Data from the Government of the Hong Kong SAR, Lands Department, via the [CSDI Portal](https://portal.csdi.gov.hk) (Building
layer, `landsd_rcd_1637211194312_35158`), used under the [CSDI Terms of Use](https://portal.csdi.gov.hk/csdi-webpage/doc/TNC).
The Government and the Lands Department own the intellectual property rights in the data. The outputs are derived from it
(reprojected to WGS84, holes resolved, a height field added, tiled). They are provided as is, with no warranty, and are not
endorsed by the Government.

Code: Apache-2.0.
