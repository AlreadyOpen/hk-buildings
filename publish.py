"""Publish the bake to Hugging Face (needs HF_TOKEN with write access to the alreadyopen org):
  dataset alreadyopen/hk-buildings  buildings.parquet (GeoParquet) + index.json, and the card (hf/README.md); one commit a run
  bucket  alreadyopen/hk-buildings  buildings.pmtiles + index.json, overwritten in place (read by browsers: CORS + HTTP Range)
  manifest.json (both): sha256 of every file, counts, sources
Nothing is uploaded unless the publish gate passes (manifest.py: no count drops > 10% against the published manifest).
Usage: python3 publish.py     (after buildings.py)"""
import json, os
from huggingface_hub import HfApi, batch_bucket_files, create_bucket
import manifest, sources

REPO = 'milleleaf/hk-buildings'

def main():
    o = lambda f: os.path.join(sources.OUT, f); idx = json.load(open(o('index.json')))
    m = manifest.manifest(sources.OUT, ['buildings.parquet', 'buildings.pmtiles', 'index.json'],
                          {'buildings': idx['buildings'], 'with_height': idx['with_height']}, idx['built'])
    manifest.gate(m, f'https://huggingface.co/buckets/{REPO}/resolve/manifest.json')
    json.dump(m, open(o('manifest.json'), 'w'), indent=1)
    api = HfApi(); api.create_repo(REPO, repo_type='dataset', exist_ok=True)
    api.upload_file(path_or_fileobj=o('buildings.parquet'), path_in_repo='buildings.parquet', repo_id=REPO, repo_type='dataset', commit_message=f"buildings: bake of {idx['built']}")
    api.upload_file(path_or_fileobj=o('index.json'), path_in_repo='index.json', repo_id=REPO, repo_type='dataset', commit_message='index')
    api.upload_file(path_or_fileobj=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf', 'README.md'), path_in_repo='README.md', repo_id=REPO, repo_type='dataset', commit_message='card')
    api.upload_file(path_or_fileobj=o('manifest.json'), path_in_repo='manifest.json', repo_id=REPO, repo_type='dataset', commit_message='manifest')
    create_bucket(REPO, private=False, exist_ok=True)
    batch_bucket_files(REPO, add=[(o('buildings.pmtiles'), 'buildings.pmtiles'), (o('index.json'), 'index.json'), (o('manifest.json'), 'manifest.json')])   # the gate reads the bucket's
    print(json.dumps({'dataset': f'https://huggingface.co/datasets/{REPO}', 'bucket': f'https://huggingface.co/buckets/{REPO}', 'built': idx['built'], 'counts': m['counts']}))

if __name__ == '__main__':
    main()
