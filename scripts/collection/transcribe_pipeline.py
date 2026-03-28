#!/usr/bin/env python3
"""
Transcription Pipeline
Transcribes audio/video (YouTube, local files) using OpenAI Whisper.
Free, runs locally on Apple Silicon via MLX.

Install:
  pip install openai-whisper yt-dlp
  # For Apple Silicon (faster):
  pip install mlx-whisper
"""

import whisper
import yt_dlp
import json, os, logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)

BASE_DIR  = Path(__file__).parent.parent.parent
OUT_DIR   = BASE_DIR / "data" / "raw" / "religious_texts"
AUDIO_TMP = BASE_DIR / "logs" / "audio_tmp"
AUDIO_TMP.mkdir(parents=True, exist_ok=True)

_model = None

def load_whisper(model_size="large"):
    global _model
    if _model is None:
        log.info(f"Loading Whisper model: {model_size}")
        _model = whisper.load_model(model_size)
    return _model

def download_audio(url, out_path):
    """Download audio from a YouTube URL."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_path),
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get("title", "unknown")

def transcribe_youtube(url, language=None, source_name="", source_perspective="", category="religious_texts", pilot_conflicts=None):
    """Download and transcribe a YouTube video, save as JSONL record."""
    audio_path = AUDIO_TMP / "temp_audio.mp3"
    log.info(f"Downloading: {url}")
    title = download_audio(url, str(AUDIO_TMP / "temp_audio"))

    log.info(f"Transcribing: {title}")
    model = load_whisper()
    result = model.transcribe(str(audio_path), language=language)

    record = {
        "id": f"yt_{hash(url) % 10**8}",
        "source_name": source_name or title,
        "source_url": url,
        "source_country": "",
        "source_perspective": source_perspective,
        "date": datetime.utcnow().isoformat(),
        "language": result.get("language", language or "unknown"),
        "category": category,
        "pilot_conflicts": pilot_conflicts or [],
        "conflict_types": [],
        "text": result["text"],
        "transcript_segments": result.get("segments", []),
        "translation_required": result.get("language", "en") != "en",
        "confidence": "high",
        "notes": f"Whisper transcription of: {title}",
        "collected_at": datetime.utcnow().isoformat()
    }

    out_path = OUT_DIR / f"transcript_{record['id']}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if audio_path.exists():
        audio_path.unlink()

    log.info(f"Saved transcript: {out_path.name} ({len(result['text'])} chars)")
    return record

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example: transcribe a public lecture
    # transcribe_youtube(
    #     url="https://www.youtube.com/watch?v=EXAMPLE",
    #     source_name="Nouman Ali Khan — Lecture",
    #     source_perspective="Sunni-Islamic-scholar",
    #     pilot_conflicts=["iran_hormuz", "afghanistan"]
    # )
    print("Transcription pipeline ready. Pass a YouTube URL to transcribe_youtube().")
