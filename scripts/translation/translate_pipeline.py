#!/usr/bin/env python3
"""
Translation Pipeline
Translates Dari, Persian (Farsi), and Arabic text to English
using Helsinki-NLP opus-mt models (free, runs locally on Apple Silicon).

Install: pip install transformers torch sentencepiece
Models download automatically on first run (~500MB each).
"""

from transformers import MarianMTModel, MarianTokenizer
from pathlib import Path
import json, logging

log = logging.getLogger(__name__)

# ─── Model registry ───────────────────────────────────────────────────────────
# Helsinki-NLP models: https://huggingface.co/Helsinki-NLP

MODELS = {
    "fa": "Helsinki-NLP/opus-mt-fa-en",   # Persian/Farsi → English (also covers Dari)
    "ar": "Helsinki-NLP/opus-mt-ar-en",   # Arabic → English
    "ru": "Helsinki-NLP/opus-mt-ru-en",   # Russian → English
    "zh": "Helsinki-NLP/opus-mt-zh-en",   # Chinese → English
}

_loaded_models = {}

def get_model(lang_code):
    """Lazy-load translation model for a given language."""
    if lang_code not in _loaded_models:
        model_name = MODELS.get(lang_code)
        if not model_name:
            log.warning(f"No translation model for language: {lang_code}")
            return None, None
        log.info(f"Loading translation model: {model_name}")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        _loaded_models[lang_code] = (model, tokenizer)
    return _loaded_models[lang_code]

def translate(text, source_lang, max_length=512):
    """Translate text from source_lang to English."""
    if source_lang == "en":
        return text
    model, tokenizer = get_model(source_lang)
    if not model:
        return text
    try:
        # Split long texts into chunks
        sentences = text.split(". ")
        chunks, current = [], ""
        for s in sentences:
            if len(current) + len(s) < max_length:
                current += s + ". "
            else:
                if current:
                    chunks.append(current.strip())
                current = s + ". "
        if current:
            chunks.append(current.strip())

        translated = []
        for chunk in chunks:
            tokens = tokenizer([chunk], return_tensors="pt", padding=True, truncation=True)
            output = model.generate(**tokens)
            translated.append(tokenizer.decode(output[0], skip_special_tokens=True))
        return " ".join(translated)
    except Exception as e:
        log.error(f"Translation failed ({source_lang}): {e}")
        return text

def translate_jsonl_file(input_path, output_path=None):
    """Translate all records in a JSONL file that need translation."""
    input_path = Path(input_path)
    if not output_path:
        output_path = input_path.parent / f"translated_{input_path.name}"

    translated_count = 0
    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            record = json.loads(line)
            if record.get("translation_required") and record.get("language") != "en":
                lang = record["language"]
                record["text_original"] = record["text"]
                record["text"] = translate(record["text"], lang)
                record["translated"] = True
                translated_count += 1
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")

    log.info(f"Translated {translated_count} records → {output_path}")
    return output_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with a sample
    test_fa = "ایران یک کشور بزرگ در خاورمیانه است"
    print(f"Persian input:  {test_fa}")
    print(f"English output: {translate(test_fa, 'fa')}")
