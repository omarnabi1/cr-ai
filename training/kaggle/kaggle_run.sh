#!/usr/bin/env bash
# Pilot fine-tune on Kaggle's free GPUs, driven from your Mac.
# Needs ~/.kaggle/kaggle.json (kaggle.com → Settings → API → Create New Token) and `pip install kaggle`.
#   ./kaggle_run.sh push     upload training data + start the GPU run
#   ./kaggle_run.sh status   check the run
#   ./kaggle_run.sh pull     download the trained adapter to ./adapter
set -euo pipefail
cd "$(dirname "$0")"
USER_NAME=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.kaggle/kaggle.json')))['username'])")
DATA_SLUG="$USER_NAME/cr-ai-crp"
KERNEL_SLUG="$USER_NAME/cr-ai-crp-lora"
case "${1:-}" in
  push)
    mkdir -p build/data build/kernel
    cp ../crp/train.jsonl ../crp/val.jsonl build/data/
    cat > build/data/dataset-metadata.json <<JSON
{"title": "cr-ai-crp", "id": "$DATA_SLUG", "licenses": [{"name": "CC-BY-4.0"}]}
JSON
    kaggle datasets create -p build/data -q 2>/dev/null || kaggle datasets version -p build/data -m "update" -q
    cp train_crp_lora.py build/kernel/
    cat > build/kernel/kernel-metadata.json <<JSON
{"id": "$KERNEL_SLUG", "title": "cr-ai-crp-lora", "code_file": "train_crp_lora.py", "language": "python", "kernel_type": "script",
 "is_private": true, "enable_gpu": true, "enable_internet": true, "dataset_sources": ["$DATA_SLUG"], "competition_sources": [], "kernel_sources": []}
JSON
    sleep 20  # give the dataset a moment to process
    kaggle kernels push -p build/kernel
    ;;
  status) kaggle kernels status "$KERNEL_SLUG" ;;
  pull) mkdir -p out && kaggle kernels output "$KERNEL_SLUG" -p out && ls -la out/adapter ;;
  *) echo "usage: $0 push|status|pull"; exit 1 ;;
esac
