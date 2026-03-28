#!/usr/bin/env python3
"""
CR-AI Base Model Selection — Phase 1 Task 3
Evaluates and documents the chosen base model for fine-tuning.

Decision: Mistral-7B-Instruct-v0.3 (open source, commercial license)
Rationale documented below. Can be swapped for Llama-3-8B-Instruct.

Install: pip install huggingface_hub transformers accelerate bitsandbytes
"""

# ─── MODEL DECISION RECORD ───────────────────────────────────────────────────
#
# Evaluated candidates:
#
# 1. Mistral-7B-Instruct-v0.3       ← SELECTED
#    License: Apache 2.0 (commercial OK)
#    Size: 7B params, ~14GB fp16, ~4GB 4-bit quantized
#    Strengths: Strong instruction following, multilingual capability,
#               sliding window attention handles long conflict documents,
#               runs on Mac M-series with llama.cpp / MLX
#    Context: 32k tokens (fits long diplomatic cables, UN reports)
#
# 2. Llama-3-8B-Instruct             ← Strong alternative
#    License: Meta Llama 3 Community (commercial OK with restrictions)
#    Size: 8B params
#    Strengths: Strong reasoning, good multilingual
#    Weaknesses: Slightly larger, Meta license terms more complex
#
# 3. Anthropic Claude API            ← Rejected for fine-tuning
#    No fine-tuning API available for our use case at this time
#    Used for taxonomy review cycles only
#
# 4. GPT-4 fine-tuning               ← Rejected
#    Cost prohibitive, proprietary, not self-hostable
#
# FINE-TUNING STRATEGY:
#   Method: QLoRA (Quantized Low-Rank Adaptation)
#   Why: Runs on Apple Silicon (M1/M2/M3), low VRAM requirement (~8GB)
#   Library: Hugging Face PEFT + trl (SFTTrainer)
#   Training data format: instruction-response pairs from taxonomy + collected data
#
# HARDWARE NOTES (Phase 1 Task 4):
#   Recommended: Mac mini M2 Pro (16GB unified memory) or Mac Studio M2 Max
#   Current dev machine: Omar's MacBook Pro (Apple Silicon, arm64)
#   Inference: llama.cpp with Metal backend OR mlx-lm
#   Training: MLX-LM fine-tuning (Apple's ML framework, optimized for M-series)
#
# ─────────────────────────────────────────────────────────────────────────────

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
FALLBACK_MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
QUANTIZATION = "4bit"  # For local inference on Apple Silicon

import json
from pathlib import Path
from datetime import datetime

DOCS_DIR = Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)

def write_model_decision():
    """Write the model selection decision to docs/."""
    decision = {
        "decided_at": datetime.utcnow().isoformat(),
        "phase": "Phase 1 Task 3",
        "selected_model": {
            "id": MODEL_ID,
            "provider": "Mistral AI",
            "license": "Apache 2.0",
            "parameters": "7B",
            "context_window": 32768,
            "quantization_for_inference": QUANTIZATION,
            "fine_tuning_method": "QLoRA",
            "fine_tuning_library": "huggingface/peft + trl",
            "inference_backend": "mlx-lm (Apple Silicon) or llama.cpp"
        },
        "fallback_model": FALLBACK_MODEL_ID,
        "rejected_models": [
            {"id": "gpt-4", "reason": "Proprietary, not self-hostable, cost prohibitive"},
            {"id": "claude-3", "reason": "No fine-tuning API available"},
            {"id": "gemini-pro", "reason": "Proprietary, API-only"}
        ],
        "training_data_format": "instruction_response_pairs",
        "estimated_training_time": "4-8 hours on M2 Pro with QLoRA 4-bit",
        "notes": "Model will be fine-tuned on CR-AI taxonomy + collected conflict dataset"
    }
    out = DOCS_DIR / "model_decision.json"
    with open(out, "w") as f:
        json.dump(decision, f, indent=2)
    print(f"Model decision saved → {out}")
    return decision

def check_model_available():
    """Check if the model can be downloaded / is already cached."""
    try:
        from huggingface_hub import model_info
        info = model_info(MODEL_ID)
        print(f"Model available: {info.id}")
        print(f"Downloads: {getattr(info, 'downloads', 'N/A')}")
        return True
    except Exception as e:
        print(f"Cannot reach HuggingFace Hub: {e}")
        return False

def download_model_for_inference():
    """
    Download and quantize Mistral-7B for local inference on Apple Silicon.
    Uses mlx-lm for MLX-native inference.
    """
    try:
        import subprocess
        print("Converting Mistral-7B to MLX 4-bit format for Apple Silicon...")
        result = subprocess.run([
            "python3", "-m", "mlx_lm.convert",
            "--hf-path", MODEL_ID,
            "--mlx-path", "models/mistral-7b-4bit",
            "-q"  # quantize to 4-bit
        ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
        if result.returncode == 0:
            print("Model downloaded and quantized successfully.")
            print(f"Saved to: models/mistral-7b-4bit")
        else:
            print(f"Conversion error: {result.stderr}")
    except ImportError:
        print("mlx_lm not installed. Run: pip install mlx-lm")

def test_inference():
    """Quick test of the downloaded model."""
    try:
        from mlx_lm import load, generate
        model_path = str(Path(__file__).parent.parent / "models" / "mistral-7b-4bit")
        print(f"Loading model from {model_path}...")
        model, tokenizer = load(model_path)
        prompt = """You are CR-AI, a conflict resolution analysis system.
Analyze the following conflict and identify its primary drivers:
The Strait of Hormuz dispute involves Iran threatening to close the strait in response to US sanctions.

Analysis:"""
        response = generate(model, tokenizer, prompt=prompt, max_tokens=200, verbose=False)
        print("\n=== TEST INFERENCE ===")
        print(response)
        return True
    except Exception as e:
        print(f"Inference test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    decision = write_model_decision()
    print(json.dumps(decision, indent=2))

    if "--download" in sys.argv:
        check_model_available()
        download_model_for_inference()

    if "--test" in sys.argv:
        test_inference()
