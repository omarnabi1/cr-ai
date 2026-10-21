# CR-AI pilot fine-tune: QLoRA on Mistral-7B-Instruct-v0.2, run free on a Kaggle T4/P100.
# The adapter is sized for Cloudflare Workers AI custom LoRAs (rank <= 8, safetensors < 300MB),
# so the trained model can be served for free at the edge.
#
# Run by kaggle_run.sh: the training data goes up as a private Kaggle dataset, this script runs as a
# GPU kernel, and the adapter comes back down as kernel output. No secrets live on Kaggle.
# Input: /kaggle/input/cr-ai-crp/{train,val}.jsonl. Output: /kaggle/working/adapter.

import json
import os
import subprocess
import sys

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "unsloth", "trl>=0.9", "datasets"], check=True)

from datasets import load_dataset  # noqa: E402
from trl import SFTConfig, SFTTrainer  # noqa: E402
from unsloth import FastLanguageModel  # noqa: E402

BASE = "unsloth/mistral-7b-instruct-v0.2-bnb-4bit"  # same weights as the Workers AI LoRA base
DATA = "/kaggle/input/cr-ai-crp"
MAX_LEN = 3072

ds = load_dataset("json", data_files={s: f"{DATA}/{s}.jsonl" for s in ("train", "val")})

model, tok = FastLanguageModel.from_pretrained(BASE, max_seq_length=MAX_LEN, load_in_4bit=True)
model = FastLanguageModel.get_peft_model(
    model,
    r=8,  # Workers AI accepts rank <= 8 on every LoRA base
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    use_gradient_checkpointing="unsloth",
)


def fmt(ex):
    # Mistral v0.2 has no system role: fold the system prompt into the first user turn.
    msgs = ex["messages"]
    sys_txt = next((m["content"] for m in msgs if m["role"] == "system"), "")
    turns = [m for m in msgs if m["role"] != "system"]
    if sys_txt and turns and turns[0]["role"] == "user":
        turns[0] = {"role": "user", "content": sys_txt + "\n\n" + turns[0]["content"]}
    return {"text": tok.apply_chat_template(turns, tokenize=False)}


ds = ds.map(fmt, remove_columns=ds["train"].column_names)

trainer = SFTTrainer(
    model=model,
    tokenizer=tok,
    train_dataset=ds["train"],
    eval_dataset=ds["val"],
    args=SFTConfig(
        output_dir="out",
        dataset_text_field="text",
        max_seq_length=MAX_LEN,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=3,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="no",
        fp16=True,
        report_to="none",
    ),
)
stats = trainer.train()
metrics = trainer.evaluate()
print(json.dumps({"train": stats.metrics, "eval": metrics}, indent=1))

os.makedirs("/kaggle/working/adapter", exist_ok=True)
os.chdir("/kaggle/working")
model.save_pretrained("adapter")
tok.save_pretrained("adapter")
# Workers AI wants exactly adapter_config.json + adapter_model.safetensors with model_type set.
cfg_path = "adapter/adapter_config.json"
cfg = json.load(open(cfg_path))
cfg["model_type"] = "mistral"
json.dump(cfg, open(cfg_path, "w"), indent=1)
json.dump({"train": stats.metrics, "eval": metrics}, open("adapter/metrics.json", "w"), indent=1)

print("adapter saved to /kaggle/working/adapter")
