#!/usr/bin/env python3
"""
HuggingFace Dataset Upload Script — CR-AI
Syncs all local JSONL data files to a private HuggingFace dataset repo.
Called by every GitHub Actions workflow after collection.

Setup:
  1. Create account at https://huggingface.co
  2. Create new dataset repo (private): huggingface.co/new-dataset
     Name it: cr-ai-dataset
  3. Generate token at: huggingface.co/settings/tokens
     Permissions: write access to repos
  4. Add to GitHub secrets: HF_TOKEN and HF_DATASET_REPO

Install: pip install huggingface_hub
"""

import os, json, logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

HF_TOKEN        = os.getenv("HF_TOKEN", "")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "")  # e.g. "omarnabi/cr-ai-dataset"

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

def upload_to_huggingface():
    """Upload all JSONL files from data/raw/ to HuggingFace dataset repo."""
    if not HF_TOKEN or not HF_DATASET_REPO:
        log.error("HF_TOKEN or HF_DATASET_REPO not set. Skipping upload.")
        log.error("  Set HF_TOKEN and HF_DATASET_REPO as env vars or GitHub secrets.")
        return False

    try:
        from huggingface_hub import HfApi
    except ImportError:
        log.error("huggingface_hub not installed. Run: pip install huggingface_hub")
        return False

    api = HfApi(token=HF_TOKEN)

    # Verify repo exists, create if not
    try:
        api.repo_info(repo_id=HF_DATASET_REPO, repo_type="dataset")
        log.info(f"Dataset repo found: {HF_DATASET_REPO}")
    except Exception:
        log.info(f"Creating dataset repo: {HF_DATASET_REPO}")
        api.create_repo(
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            private=True
        )

    # Collect all JSONL files
    jsonl_files = list(DATA_DIR.rglob("*.jsonl"))
    if not jsonl_files:
        log.warning("No JSONL files found in data/raw/")
        return True

    log.info(f"Uploading {len(jsonl_files)} files to {HF_DATASET_REPO}...")

    total_records = 0
    upload_errors = 0

    for local_path in jsonl_files:
        # Preserve directory structure: data/raw/social_media/reddit_iran.jsonl
        # → becomes: data/social_media/reddit_iran.jsonl on HF
        rel_path = local_path.relative_to(DATA_DIR)
        hf_path = f"data/{rel_path}"

        try:
            line_count = sum(1 for _ in open(local_path, encoding="utf-8"))
            api.upload_file(
                path_or_fileobj=str(local_path),
                path_in_repo=hf_path,
                repo_id=HF_DATASET_REPO,
                repo_type="dataset",
                commit_message=f"sync: {rel_path} ({line_count} records) {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
            )
            total_records += line_count
            log.info(f"  ✓ {hf_path} ({line_count} records)")
        except Exception as e:
            log.error(f"  ✗ {hf_path}: {e}")
            upload_errors += 1

    # Upload taxonomy and docs too
    extras = [
        BASE_DIR / "taxonomy" / "taxonomy_v6_meta.json",
        BASE_DIR / "docs" / "actor_profile_schema.json",
        BASE_DIR / "docs" / "model_decision.json",
    ]
    for extra in extras:
        if extra.exists():
            try:
                api.upload_file(
                    path_or_fileobj=str(extra),
                    path_in_repo=f"metadata/{extra.name}",
                    repo_id=HF_DATASET_REPO,
                    repo_type="dataset",
                    commit_message=f"sync: metadata/{extra.name}"
                )
                log.info(f"  ✓ metadata/{extra.name}")
            except Exception as e:
                log.error(f"  ✗ {extra.name}: {e}")

    log.info(f"Upload complete: {total_records} total records, {upload_errors} errors")
    return upload_errors == 0


if __name__ == "__main__":
    success = upload_to_huggingface()
    exit(0 if success else 1)
