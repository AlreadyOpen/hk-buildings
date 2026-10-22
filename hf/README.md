---
pretty_name: Hong Kong buildings with heights
license: other
license_name: hk-csdi-terms-of-use
license_link: https://portal.csdi.gov.hk/csdi-webpage/doc/TNC
tags:
  - geospatial
  - buildings
  - hong-kong
  - geoparquet
size_categories:
  - 100K<n<1M
configs:
  - config_name: default
    data_files: buildings.parquet
---

# Hong Kong buildings with heights

Every building footprint in Hong Kong (about 342,000) from the Lands Department's CSDI Building layer, with each building's
own height, rebuilt weekly by [milleleaf/hk-buildings](https://github.com/milleleaf/hk-buildings).

`buildings.parquet` is GeoParquet: `geometry` (MultiPolygon, WKB, EPSG:4326) plus `BuildingCSUID`, `BuildingNameEN`,
`BuildingNameTC`, `BaseHeight` and `TopHeight` (mPD), `height_m` (= TopHeight - BaseHeight, the height above the building's
base; empty when either is missing), `Storeys`, `StoreysInBasement`, `BuildingBlockType`, `Status`.

Vector tiles of the same buildings for web maps (PMTiles, z13-16) are in the bucket
[milleleaf/hk-buildings](https://huggingface.co/buckets/milleleaf/hk-buildings).

```python
import duckdb
duckdb.sql("""SELECT BuildingNameEN, height_m FROM 'hf://datasets/milleleaf/hk-buildings/buildings.parquet'
              ORDER BY height_m DESC LIMIT 10""")
```

A copy is mirrored to [Kaggle](https://www.kaggle.com/datasets/helenkwok/hk-buildings) after every bake.

## Source and terms

Data from the Government of the Hong Kong SAR, Lands Department, via the CSDI Portal, used under the
[CSDI Terms of Use](https://portal.csdi.gov.hk/csdi-webpage/doc/TNC). The Government and the Lands Department own the
intellectual property rights in the data. This dataset is derived from it, provided as is with no warranty, and not endorsed
by the Government.
