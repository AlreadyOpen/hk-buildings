"""Every building in Hong Kong from the Lands Department's CSDI 'Building' layer (all 342k footprints, live MapServer, paged
3,000 at a time; a snapshot is reused when its content hash is unchanged), with each building's own height:
height_m = TopHeight - BaseHeight (both are mPD; TopHeight alone would add the ground under the building, ~180 m in Mid-Levels;
left empty when either is missing).
Writes, in data/out/:
  - buildings.pmtiles: vector tiles z13-16 (MapLibre overzooms past 16), tiles gzipped inside, layer 'buildings' (tippecanoe)
  - buildings.parquet: one row per building with its footprint as GeoParquet (WKB, EPSG:4326) and the same attributes, for
    queries and for zooms below 13 (e.g. tall buildings for a skyline)
  - index.json: counts, sizes, source
Usage: python3 buildings.py"""
import datetime, hashlib, json, os, subprocess, sys, urllib.parse, urllib.request
import duckdb
from pyproj import Transformer
from shapely.geometry import LinearRing, Polygon
from shapely.ops import unary_union
import sources

TO_LL = Transformer.from_crs(2326, 4326, always_xy=True)
KEEP = ('BuildingCSUID', 'BuildingNameEN', 'BuildingNameTC', 'BaseHeight', 'TopHeight', 'Storeys', 'StoreysInBasement', 'BuildingBlockType', 'Status')

def csdi_polygon(f):
    """Esri rings -> shapely: clockwise rings are outers, counter-clockwise rings are holes"""
    r = f['geometry']['rings']
    outer = unary_union([Polygon(x) for x in r if not LinearRing(x).is_ccw])
    holes = [Polygon(x) for x in r if LinearRing(x).is_ccw]
    return outer.difference(unary_union(holes)) if holes else outer

def fetch():
    """every CSDI building, paged; returns the snapshot path (data/cache/csdi/<content hash>.json)"""
    feats = []
    while True:
        q = {'where': '1=1', 'outFields': ','.join(KEEP), 'outSR': 2326, 'orderByFields': 'BuildingCSUID', 'resultOffset': len(feats),
             'resultRecordCount': 3000, 'returnGeometry': 'true', 'f': 'json'}
        for attempt in range(4):
            try: d = json.load(urllib.request.urlopen(f'{sources.BUILDINGS}?{urllib.parse.urlencode(q)}', timeout=180)); break
            except Exception:
                if attempt == 3: raise
        feats += d['features']
        if len(feats) % 30000 < 3000: print(f'buildings: {len(feats)}', file=sys.stderr, flush=True)
        if not d.get('exceededTransferLimit') or not d['features']: break
    body = json.dumps({'features': feats}, sort_keys=True, separators=(',', ':')).encode()
    p = os.path.join(sources.CACHE, 'csdi', f'{hashlib.sha256(body).hexdigest()[:16]}.json')
    if not os.path.exists(p): os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(body)
    return p

def main():
    snap = fetch(); feats = json.load(open(snap))['features']
    os.makedirs(sources.OUT, exist_ok=True)
    src = os.path.join(sources.CACHE, 'csdi', 'buildings.geojsonl'); n = 0
    with open(src, 'w') as f:
        for x in feats:
            a = x['attributes']; g = csdi_polygon(x)
            if g.is_empty: continue
            ll = lambda cs: [[round(v, 7) for v in TO_LL.transform(px, py)] for px, py in cs]
            geom = {'type': 'MultiPolygon', 'coordinates': [[ll(q.exterior.coords)] + [ll(h.coords) for h in q.interiors] for q in getattr(g, 'geoms', [g])]}
            t, b = a.get('TopHeight'), a.get('BaseHeight')   # both mPD; 1,547 lack BaseHeight (2026-10-10): height unknown, not TopHeight
            p = {k: a.get(k) for k in KEEP} | {'height_m': round(max(0.0, t - b), 1) if t is not None and b is not None else None}
            f.write(json.dumps({'type': 'Feature', 'properties': {k: v for k, v in p.items() if v is not None}, 'geometry': geom}, ensure_ascii=False) + '\n'); n += 1
    tiles = os.path.join(sources.OUT, 'buildings.pmtiles')
    subprocess.run(['tippecanoe', '-o', tiles + '.part.pmtiles', '-l', 'buildings', '-Z13', '-z16', '--drop-densest-as-needed',
                    '--extend-zooms-if-still-dropping', '--force', '--quiet', src], check=True)
    os.replace(tiles + '.part.pmtiles', tiles)
    # GeoParquet: DuckDB's spatial extension writes the GEOMETRY column as WKB with GeoParquet metadata
    pq = os.path.join(sources.OUT, 'buildings.parquet'); c = duckdb.connect(); c.execute('INSTALL spatial; LOAD spatial')
    cols = ', '.join(f"properties->>'{k}' AS {k}" for k in ('BuildingCSUID', 'BuildingNameEN', 'BuildingNameTC', 'BuildingBlockType', 'Status'))
    nums = ', '.join(f"TRY_CAST(properties->>'{k}' AS {t}) AS {k}" for k, t in (('BaseHeight', 'DOUBLE'), ('TopHeight', 'DOUBLE'), ('height_m', 'DOUBLE'), ('Storeys', 'INTEGER'), ('StoreysInBasement', 'INTEGER')))
    c.execute(f"""COPY (SELECT {cols}, {nums}, ST_GeomFromGeoJSON(geometry::VARCHAR) AS geometry
                  FROM read_json('{src}', format = 'newline_delimited', columns = {{properties: 'JSON', geometry: 'JSON'}}) ORDER BY BuildingCSUID)
                  TO '{pq}.part' (FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 16384)""")
    os.replace(pq + '.part', pq)
    rows = c.execute(f"SELECT count(*), count(*) FILTER (WHERE height_m > 0), max(height_m) FROM '{pq}'").fetchone()
    idx = {'built': datetime.datetime.now().isoformat(timespec='seconds'), 'buildings': n, 'parquet_rows': rows[0], 'with_height': rows[1], 'tallest_m': rows[2],
           'pmtiles': {'file': 'buildings.pmtiles', 'layer': 'buildings', 'minzoom': 13, 'maxzoom': 16, 'MB': round(os.path.getsize(tiles) / 1e6, 1)},
           'parquet': {'file': 'buildings.parquet', 'MB': round(os.path.getsize(pq) / 1e6, 1), 'crs': 'EPSG:4326'},
           'source': f'Lands Department, CSDI Building layer (landsd_rcd_1637211194312_35158), snapshot {os.path.basename(snap)}, tippecanoe 2.79.0'}
    json.dump(idx, open(os.path.join(sources.OUT, 'index.json'), 'w'), indent=1)
    print(json.dumps(idx))

if __name__ == '__main__':
    main()
