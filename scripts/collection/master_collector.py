#!/usr/bin/env python3
"""
CR-AI Master Data Collector
Phase 2 — Dataset collection for Iran/Hormuz and Afghanistan pilot conflicts
"""

import os
import json
import hashlib
import logging
import requests
import feedparser
from datetime import datetime
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
LOG_DIR  = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "collection.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── Standard JSONL output schema ────────────────────────────────────────────

def make_record(
    source_name, source_url, source_country, source_perspective,
    date, language, category, pilot_conflicts, conflict_types, text,
    translation_required=False, confidence="medium", notes=""
):
    return {
        "id": hashlib.sha256(f"{source_name}{date}{text[:100]}".encode()).hexdigest()[:16],
        "source_name": source_name,
        "source_url": source_url,
        "source_country": source_country,
        "source_perspective": source_perspective,
        "date": date,
        "language": language,
        "category": category,
        "pilot_conflicts": pilot_conflicts,
        "conflict_types": conflict_types,
        "text": text,
        "translation_required": translation_required,
        "confidence": confidence,
        "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }

def save_record(record, category):
    """Append a record to the appropriate JSONL file."""
    out_dir = DATA_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{category}.jsonl"
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    log.info(f"Saved: {record['source_name']} → {out_path.name}")

# ─── RSS Feed Collector ───────────────────────────────────────────────────────

RSS_SOURCES = [
    # Iranian / MENA perspective
    {"name": "PressTV", "url": "https://www.presstv.ir/rss.xml",
     "country": "Iran", "perspective": "Iranian-state",
     "category": "geopolitical_lit", "pilots": ["iran_hormuz"]},

    {"name": "Tehran Times", "url": "https://www.tehrantimes.com/rss.xml",
     "country": "Iran", "perspective": "Iranian-semi-independent",
     "category": "geopolitical_lit", "pilots": ["iran_hormuz"]},

    {"name": "Al Jazeera English", "url": "https://www.aljazeera.com/xml/rss/all.xml",
     "country": "Qatar", "perspective": "Gulf-independent",
     "category": "geopolitical_lit", "pilots": ["iran_hormuz", "afghanistan"]},

    # Russian perspective
    {"name": "TASS", "url": "https://tass.com/rss/v2.xml",
     "country": "Russia", "perspective": "Russian-state",
     "category": "geopolitical_lit", "pilots": ["iran_hormuz", "afghanistan"]},

    # Afghan independent
    {"name": "Tolo News", "url": "https://tolonews.com/rss",
     "country": "Afghanistan", "perspective": "Afghan-independent",
     "category": "geopolitical_lit", "pilots": ["afghanistan"]},

    # Chinese perspective
    {"name": "Xinhua", "url": "http://www.xinhuanet.com/english/rss/worldrss.xml",
     "country": "China", "perspective": "Chinese-state",
     "category": "geopolitical_lit", "pilots": ["iran_hormuz", "afghanistan"]},
]

def collect_rss(source, limit=100):
    """Collect articles from an RSS feed source."""
    log.info(f"Collecting RSS: {source['name']}")
    try:
        feed = feedparser.parse(source["url"])
        count = 0
        for entry in feed.entries[:limit]:
            text = entry.get("summary", "") or entry.get("description", "")
            if len(text) < 50:
                continue
            record = make_record(
                source_name=source["name"],
                source_url=entry.get("link", source["url"]),
                source_country=source["country"],
                source_perspective=source["perspective"],
                date=entry.get("published", datetime.utcnow().isoformat()),
                language="en",
                category=source["category"],
                pilot_conflicts=source["pilots"],
                conflict_types=[],
                text=f"{entry.get('title','')}. {text}",
                notes=f"RSS collection from {source['name']}"
            )
            save_record(record, source["category"])
            count += 1
        log.info(f"  → {count} records from {source['name']}")
        return count
    except Exception as e:
        log.error(f"  → Failed {source['name']}: {e}")
        return 0

def run_rss_collection():
    total = 0
    for src in RSS_SOURCES:
        total += collect_rss(src)
    log.info(f"RSS collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_rss_collection()
