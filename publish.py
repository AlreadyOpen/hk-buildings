"""Publish the bake to Hugging Face (needs HF_TOKEN with write access to the alreadyopen org):
  dataset alreadyopen/hk-buildings  buildings.parquet (GeoParquet) + index.json, and the card (hf/README.md); one commit a run
  bucket  alreadyopen/hk-buildings  buildings.pmtiles + index.json, overwritten in place (read by browsers: CORS + HTTP Range)
Usage: python3 publish.py     (after buildings.py)"""
import json, os
from huggingface_hub import HfApi, batch_bucket_files, create_bucket
import sources

REPO = 'alreadyopen/hk-buildings'

def main():
    o = lambda f: os.path.join(sources.OUT, f); idx = json.load(open(o('index.json')))
    api = HfApi(); api.create_repo(REPO, repo_type='dataset', exist_ok=True)
    api.upload_file(path_or_fileobj=o('buildings.parquet'), path_in_repo='buildings.parquet', repo_id=REPO, repo_type='dataset', commit_message=f"buildings: bake of {idx['built']}")
    api.upload_file(path_or_fileobj=o('index.json'), path_in_repo='index.json', repo_id=REPO, repo_type='dataset', commit_message='index')
    api.upload_file(path_or_fileobj=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf', 'README.md'), path_in_repo='README.md', repo_id=REPO, repo_type='dataset', commit_message='card')
    create_bucket(REPO, private=False, exist_ok=True)
    batch_bucket_files(REPO, add=[(o('buildings.pmtiles'), 'buildings.pmtiles'), (o('index.json'), 'index.json')])
    print(json.dumps({'dataset': f'https://huggingface.co/datasets/{REPO}', 'bucket': f'https://huggingface.co/buckets/{REPO}', 'built': idx['built'], 'buildings': idx['buildings']}))

if __name__ == '__main__':
    main()
