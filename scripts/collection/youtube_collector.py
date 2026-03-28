#!/usr/bin/env python3
"""
Internet Archive Video Collector — CR-AI
Replaces YouTube API. Zero credentials required — fully anonymous.

Searches archive.org for video/audio items matching Iran/Afghanistan
topics including Persian, Dari, and Pashto content.
Uses the IA Scrape API (no key needed) + optional Whisper transcription.

Install: pip install internetarchive requests
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/Users/omarnabi/Desktop/CR-AI/logs/youtube.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path("/Users/omarnabi/Desktop/CR-AI/data/raw/social_media")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Internet Archive Advanced Search API — no key needed
IA_SEARCH = "https://archive.org/advancedsearch.php"

# ─── Search queries — same topics as old YouTube collector ───────────────────
SEARCHES = [
    # Iranian state media archived on IA (huge collection — PRESSTV_* identifiers)
    {
        "q": "PressTV mediatype:movies",
        "pilot": "iran_hormuz", "lang": "en", "perspective": "Iranian-state-media"
    },
    {
        "q": "subject:Iran nuclear sanctions mediatype:movies",
        "pilot": "iran_hormuz", "lang": "en", "perspective": "Iran-IA-archive"
    },
    {
        "q": "subject:Iran subject:Hormuz mediatype:movies",
        "pilot": "iran_hormuz", "lang": "en", "perspective": "Iran-Hormuz-IA"
    },
    {
        "q": "subject:Iran subject:Persian mediatype:movies",
        "pilot": "iran_hormuz", "lang": "fa", "perspective": "Persian-video-IA"
    },
    {
        "q": "subject:Iran subject:JCPOA",
        "pilot": "iran_hormuz", "lang": "en", "perspective": "Iran-nuclear-deal-IA"
    },
    # Afghan content
    {
        "q": "Afghanistan Taliban mediatype:movies",
        "pilot": "afghanistan", "lang": "en", "perspective": "Afghan-IA-archive"
    },
    {
        "q": "ToloNews mediatype:movies",
        "pilot": "afghanistan", "lang": "en", "perspective": "Afghan-independent-media"
    },
    {
        "q": "subject:Afghanistan subject:Dari mediatype:movies",
        "pilot": "afghanistan", "lang": "fa", "perspective": "Dari-video-IA"
    },
    {
        "q": "subject:Afghanistan subject:women rights mediatype:movies",
        "pilot": "afghanistan", "lang": "en", "perspective": "Afghan-human-rights-IA"
    },
    # Audio: speeches, lectures, radio
    {
        "q": "subject:Iran subject:politics mediatype:audio",
        "pilot": "iran_hormuz", "lang": "en", "perspective": "Iran-audio-IA"
    },
    {
        "q": "subject:Afghanistan subject:politics mediatype:audio",
        "pilot": "afghanistan", "lang": "en", "perspective": "Afghan-audio-IA"
    },
]

def ia_search(query, max_results=100):
    """
    Search Internet Archive via the Advanced Search API (Solr).
    Returns list of item dicts with identifier, title, description, date, etc.
    No API key required.
    """
    results = []
    page = 1
    page_size = min(max_results, 100)

    while len(results) < max_results:
        params = {
            "q": query,
            "fl[]": "identifier,title,description,subject,creator,date,mediatype,language",
            "rows": page_size,
            "page": page,
            "output": "json",
            "sort[]": "downloads desc",
        }
        try:
            resp = requests.get(IA_SEARCH, params=params, timeout=20)
            if resp.status_code != 200:
                log.warning(f"IA search returned {resp.status_code}")
                break
            data = resp.json()
            docs = data.get("response", {}).get("docs", [])
            if not docs:
                break
            results.extend(docs)
            if len(docs) < page_size:
                break
            page += 1
        except Exception as e:
            log.error(f"IA search error: {e}")
            break

    return results[:max_results]


def collect_ia_videos(cfg, max_results=100):
    """Collect video/audio metadata from Internet Archive for one query config."""
    log.info(f"IA search: {cfg['q'][:60]}...")
    items = ia_search(cfg["q"], max_results=max_results)
    log.info(f"  -> {len(items)} items found")

    out_path = OUT_DIR / f"ia_video_{cfg['pilot']}_{cfg['lang']}.jsonl"
    count = 0

    for item in items:
        identifier = item.get("identifier", "")
        title = item.get("title", "")
        desc = item.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)
        subject = item.get("subject", "")
        if isinstance(subject, list):
            subject = "; ".join(subject)
        creator = item.get("creator", "")
        if isinstance(creator, list):
            creator = "; ".join(creator)

        text = f"{title}. {desc[:800]} Subjects: {subject}".strip()
        if len(text) < 20:
            continue

        rec = {
            "id": hashlib.sha256(identifier.encode()).hexdigest()[:16],
            "platform": "internet_archive",
            "ia_identifier": identifier,
            "source_name": f"IA: {creator or title[:40]}",
            "source_url": f"https://archive.org/details/{identifier}",
            "source_country": "unknown",
            "source_perspective": cfg["perspective"],
            "date": item.get("date", ""),
            "language": cfg["lang"],
            "category": "social_media",
            "pilot_conflicts": [cfg["pilot"]],
            "conflict_types": [],
            "text": text[:3000],
            "mediatype": item.get("mediatype", ""),
            "creator": creator,
            "translation_required": cfg["lang"] != "en",
            "confidence": "medium",
            "notes": f"Internet Archive search: {cfg['q'][:80]}",
            "collected_at": datetime.utcnow().isoformat()
        }
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        count += 1

    log.info(f"  -> {count} records saved ({out_path.name})")
    return count


def run_youtube_collection():
    """Main entry point — runs all IA video/audio searches."""
    total = 0
    for cfg in SEARCHES:
        total += collect_ia_videos(cfg, max_results=100)
    log.info(f"Internet Archive video collection complete: {total} total records")
    return total


if __name__ == "__main__":
    run_youtube_collection()
