#!/usr/bin/env python3
"""
GDELT Project Collector — CR-AI
Free, no API key needed. Indexes global news in real time.
Pulls events and articles related to Iran/Hormuz and Afghanistan.

Docs: https://www.gdeltproject.org/
"""

from dotenv import load_dotenv
load_dotenv('/Users/omarnabi/Desktop/CR-AI/.env')

import requests, json, hashlib, logging, csv, io
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/Users/omarnabi/Desktop/CR-AI/logs/gdelt.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path('/Users/omarnabi/Desktop/CR-AI/data/raw/geopolitical_lit')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── GDELT Doc API — article search ─────────────────────────────────────────

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = [
    {
        "query":   "Iran Strait Hormuz sanctions nuclear",
        "pilot":   "iran_hormuz",
        "label":   "iran_hormuz_gdelt"
    },
    {
        "query":   "Iran JCPOA nuclear deal United States",
        "pilot":   "iran_hormuz",
        "label":   "iran_nuclear_gdelt"
    },
    {
        "query":   "Afghanistan Taliban US withdrawal reconstruction",
        "pilot":   "afghanistan",
        "label":   "afghanistan_gdelt"
    },
    {
        "query":   "Afghanistan Hazara persecution ISIS-K",
        "pilot":   "afghanistan",
        "label":   "hazara_gdelt"
    },
    {
        "query":   "Iran IRGC proxy Yemen Hezbollah",
        "pilot":   "iran_hormuz",
        "label":   "iran_proxy_gdelt"
    },
]

def collect_gdelt_articles(query_cfg, max_records=250):
    """Pull articles from GDELT Doc API for a given query."""
    params = {
        "query":      query_cfg["query"],
        "mode":       "artlist",
        "maxrecords": max_records,
        "format":     "json",
        "timespan":   "1year",        # last 12 months
        "sort":       "DateDesc",
    }
    log.info(f"GDELT query: '{query_cfg['query']}'")
    try:
        r = requests.get(GDELT_DOC_API, params=params, timeout=30)
        data = r.json()
        articles = data.get("articles", [])
        log.info(f"  -> {len(articles)} articles returned")

        out_path = OUT_DIR / f"{query_cfg['label']}.jsonl"
        count = 0
        for art in articles:
            text = art.get("title", "") + ". " + art.get("seendate", "")
            if len(text) < 10:
                continue
            rec = {
                "id": hashlib.sha256(
                    art.get("url", text).encode()
                ).hexdigest()[:16],
                "source_name":        art.get("domain", "GDELT"),
                "source_url":         art.get("url", ""),
                "source_country":     art.get("sourcecountry", "unknown"),
                "source_perspective": f"GDELT-{art.get('sourcecountry','unknown')}",
                "date":               art.get("seendate", ""),
                "language":           art.get("language", "English").lower()[:2],
                "category":           "geopolitical_lit",
                "pilot_conflicts":    [query_cfg["pilot"]],
                "conflict_types":     [],
                "text":               art.get("title", ""),
                "gdelt_tone":         art.get("tone", 0),
                "gdelt_domain":       art.get("domain", ""),
                "translation_required": art.get("language","English").lower() not in ["english","en"],
                "confidence":         "medium",
                "notes":              f"GDELT query: {query_cfg['query']}",
                "collected_at":       datetime.utcnow().isoformat()
            }
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
        log.info(f"  -> {count} records saved to {out_path.name}")
        return count
    except Exception as e:
        log.error(f"  -> GDELT failed: {e}")
        return 0

def run_gdelt_collection():
    total = 0
    for q in QUERIES:
        total += collect_gdelt_articles(q)
    log.info(f"GDELT collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_gdelt_collection()
