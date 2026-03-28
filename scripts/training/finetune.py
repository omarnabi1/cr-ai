#!/usr/bin/env python3
"""
CR-AI Fine-Tuning Script — Phase 3 Step 2
QLoRA fine-tuning of Mistral-7B using MLX-LM (Apple Silicon native).

Requirements:
  pip install mlx-lm

Hardware: Mac with Apple Silicon (M1/M2/M3) — 16GB+ unified memory recommended
Time: ~4-8 hours for full run on M2 Pro

Run:
  # Step 1: Download base model (one-time, ~4GB)
  python3 scripts/training/finetune.py --download

  # Step 2: Run fine-tuning
  python3 scripts/training/finetune.py --train

  # Step 3: Test the model
  python3 scripts/training/finetune.py --test
"""

import json, logging, subprocess, sys, os
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR   = Path(__file__).parent.parent.parent
TRAIN_DIR  = BASE_DIR / "data" / "training"
MODEL_DIR  = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

BASE_MODEL    = "mistralai/Mistral-7B-Instruct-v0.3"
MODEL_4BIT    = str(MODEL_DIR / "mistral-7b-4bit")
ADAPTER_DIR   = str(MODEL_DIR / "cr-ai-adapter")
FUSED_DIR     = str(MODEL_DIR / "cr-ai-fused")

def download_and_quantize():
    """Download Mistral-7B and quantize to 4-bit for Apple Silicon."""
    log.info(f"Downloading and quantizing {BASE_MODEL}...")
    log.info("This will take ~10-20 minutes and use ~4GB disk space.")

    result = subprocess.run([
        sys.executable, "-m", "mlx_lm.convert",
        "--hf-path", BASE_MODEL,
        "--mlx-path", MODEL_4BIT,
        "-q"  # 4-bit quantization
    ], cwd=str(BASE_DIR))

    if result.returncode == 0:
        log.info(f"Model ready at: {MODEL_4BIT}")
    else:
        log.error("Download failed. Check internet connection and HuggingFace access.")
        sys.exit(1)


def prepare_mlx_training_data():
    """
    MLX-LM expects data in a specific format.
    Converts our training JSONL to MLX format.
    """
    log.info("Preparing MLX training data format...")
    mlx_train = TRAIN_DIR / "mlx_train.jsonl"
    mlx_val   = TRAIN_DIR / "mlx_val.jsonl"

    for src, dst in [(TRAIN_DIR/"train.jsonl", mlx_train), (TRAIN_DIR/"val.jsonl", mlx_val)]:
        count = 0
        with open(src, encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
            for line in fin:
                rec = json.loads(line)
                # MLX-LM expects {"text": "..."} format
                mlx_rec = {"text": rec["text"]}
                fout.write(json.dumps(mlx_rec, ensure_ascii=False) + "\n")
                count += 1
        log.info(f"  {dst.name}: {count} examples")

    return str(TRAIN_DIR)


def run_finetuning():
    """Run QLoRA fine-tuning via MLX-LM."""
    data_dir = prepare_mlx_training_data()

    log.info("Starting QLoRA fine-tuning...")
    log.info(f"Base model: {MODEL_4BIT}")
    log.info(f"Data dir:   {data_dir}")
    log.info(f"Output:     {ADAPTER_DIR}")
    log.info("Estimated time: 4-8 hours on M2 Pro")

    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model",        MODEL_4BIT,
        "--train",
        "--data",         data_dir,
        "--adapter-path", ADAPTER_DIR,
        "--num-layers",   "16",        # LoRA on 16 layers
        "--batch-size",   "4",
        "--iters",        "1000",      # adjust based on results
        "--learning-rate","1e-4",
        "--steps-per-report", "50",
        "--steps-per-eval",   "200",
        "--val-batches",      "25",
        "--save-every",       "200",
    ]

    log.info(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))

    if result.returncode == 0:
        log.info(f"Fine-tuning complete! Adapter saved to: {ADAPTER_DIR}")
        fuse_model()
    else:
        log.error("Fine-tuning failed.")
        sys.exit(1)


def fuse_model():
    """Fuse LoRA adapter into base model for deployment."""
    log.info("Fusing adapter into base model...")
    result = subprocess.run([
        sys.executable, "-m", "mlx_lm.fuse",
        "--model",        MODEL_4BIT,
        "--adapter-path", ADAPTER_DIR,
        "--save-path",    FUSED_DIR,
    ], cwd=str(BASE_DIR))

    if result.returncode == 0:
        log.info(f"Fused model saved to: {FUSED_DIR}")
        log.info("Ready for inference and API deployment!")
    else:
        log.error("Fusion failed — adapter still usable for inference")


def test_inference(prompt=None):
    """Quick test of the fine-tuned model."""
    try:
        from mlx_lm import load, generate
    except ImportError:
        log.error("mlx_lm not installed. Run: pip install mlx-lm")
        return

    # Use fused model if available, otherwise base + adapter
    model_path = FUSED_DIR if Path(FUSED_DIR).exists() else MODEL_4BIT
    adapter    = None if Path(FUSED_DIR).exists() else ADAPTER_DIR

    log.info(f"Loading model from {model_path}...")
    if adapter and Path(adapter).exists():
        model, tokenizer = load(model_path, adapter_path=adapter)
    else:
        model, tokenizer = load(model_path)

    test_prompts = prompt or [
        "Analyze the Iran nuclear dispute using the CR-AI taxonomy. What are the primary structural drivers?",
        "What resolution frameworks would you recommend for the Afghanistan conflict?",
        "Map the actor positions in the Strait of Hormuz dispute, distinguishing public and private interests.",
    ]

    if isinstance(test_prompts, str):
        test_prompts = [test_prompts]

    for p in test_prompts:
        print(f"\n{'='*60}")
        print(f"PROMPT: {p}")
        print(f"{'='*60}")
        full_prompt = f"<s>[INST] {p} [/INST]"
        response = generate(model, tokenizer, prompt=full_prompt, max_tokens=500, verbose=False)
        print(response)


def save_training_log():
    """Save training run metadata."""
    log_path = MODEL_DIR / "training_log.json"
    entry = {
        "run_at": datetime.utcnow().isoformat(),
        "base_model": BASE_MODEL,
        "adapter_path": ADAPTER_DIR,
        "fused_path": FUSED_DIR,
        "training_pairs": 11932,
        "method": "QLoRA via MLX-LM",
        "lora_layers": 16,
        "batch_size": 4,
        "iterations": 1000,
        "learning_rate": "1e-4"
    }
    with open(log_path, "w") as f:
        json.dump(entry, f, indent=2)
    log.info(f"Training log saved → {log_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CR-AI Fine-tuning")
    parser.add_argument("--download", action="store_true", help="Download + quantize base model")
    parser.add_argument("--train",    action="store_true", help="Run QLoRA fine-tuning")
    parser.add_argument("--test",     action="store_true", help="Test inference")
    parser.add_argument("--prompt",   type=str,            help="Custom test prompt")
    args = parser.parse_args()

    if args.download:
        download_and_quantize()
    elif args.train:
        if not Path(MODEL_4BIT).exists():
            log.error(f"Base model not found at {MODEL_4BIT}. Run --download first.")
            sys.exit(1)
        run_finetuning()
        save_training_log()
    elif args.test:
        test_inference(args.prompt)
    else:
        print(__doc__)
