#!/usr/bin/env python3
"""
Historical Conflict Records Collector — CR-AI Phase 2
Sources:
  - GDELT Document API (free, no key) — news/event articles by date range
  - Internet Archive (free, no key) — UN reports, SIPRI, academic conflict data
  - Global Conflict Tracker via IA — CFR conflict summaries

ACLED/UCDP require keys — add to .env when available:
  ACLED_API_KEY + ACLED_EMAIL → https://developer.acleddata.com (free)
"""

import os, json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(Path(__file__).parent.parent.parent / "logs" / "historical.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw" / "historical_conflicts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ACLED_KEY   = os.getenv("ACLED_API_KEY", "")
ACLED_EMAIL = os.getenv("ACLED_EMAIL", "")

# ── GDELT DOC API — key event periods for both pilots ──────────────────────
GDELT_QUERIES = [
    # Afghanistan
    {"q": "Afghanistan Taliban takeover Kabul",       "pilot": "afghanistan", "start": "20210801000000", "end": "20211001000000"},
    {"q": "Afghanistan US withdrawal Doha agreement", "pilot": "afghanistan", "start": "20200201000000", "end": "20210901000000"},
    {"q": "Afghanistan Taliban human rights women",   "pilot": "afghanistan", "start": "20211001000000", "end": "20221201000000"},
    {"q": "Afghanistan Hazara persecution killings",  "pilot": "afghanistan", "start": "20210801000000", "end": "20231201000000"},
    {"q": "Afghanistan economic collapse famine",     "pilot": "afghanistan", "start": "20211001000000", "end": "20231201000000"},
    # Iran / Hormuz
    {"q": "Iran nuclear deal JCPOA negotiations",     "pilot": "iran_hormuz", "start": "20190101000000", "end": "20221201000000"},
    {"q": "Iran Hormuz strait tanker seizure threat", "pilot": "iran_hormuz", "start": "20190601000000", "end": "20231201000000"},
    {"q": "Iran sanctions oil exports economy",       "pilot": "iran_hormuz", "start": "20180501000000", "end": "20231201000000"},
    {"q": "Iran protests uprising 2019 2022",         "pilot": "iran_hormuz", "start": "20191101000000", "end": "20230101000000"},
    {"q": "Iran proxy war Yemen Lebanon Hezbollah",   "pilot": "iran_hormuz", "start": "20190101000000", "end": "20231201000000"},
]

def collect_gdelt_doc():
    """
    GDELT Document API — full-text article search with date range.
    Returns article metadata + summaries. Free, no key needed.
    """
    log.info("Collecting historical conflict data via GDELT DOC API...")
    count = 0
    out_path = OUT_DIR / "gdelt_historical.jsonl"

    for q in GDELT_QUERIES:
        try:
            params = {
                "query": q["q"],
                "mode": "ArtList",
                "maxrecords": 75,
                "format": "json",
                "startdatetime": q["start"],
                "enddatetime": q["end"],
            }
            resp = requests.get("https://api.gdeltproject.org/api/v2/doc/doc",
                                params=params, timeout=20)
            if resp.status_code != 200:
                log.warning(f"GDELT DOC '{q['q'][:40]}': HTTP {resp.status_code}")
                continue
            articles = resp.json().get("articles", [])
            log.info(f"  GDELT '{q['q'][:50]}': {len(articles)} articles")
            for art in articles:
                text = f"{art.get('title', '')}. {art.get('seendate', '')} — {art.get('url', '')}"
                rec = {
                    "id": hashlib.sha256((art.get("url","") + art.get("seendate","")).encode()).hexdigest()[:16],
                    "source_name": art.get("domain", "GDELT"),
                    "source_url": art.get("url", ""),
                    "source_country": art.get("sourcecountry", ""),
                    "source_perspective": "Historical-GDELT",
                    "date": art.get("seendate", ""),
                    "language": art.get("language", "English"),
                    "category": "historical_conflicts",
                    "pilot_conflicts": [q["pilot"]],
                    "conflict_types": [],
                    "text": art.get("title", "")[:1000],
                    "gdelt_query": q["q"],
                    "confidence": "medium",
                    "notes": f"GDELT DOC API: {q['q']}",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"GDELT DOC '{q['q'][:40]}': {e}")

    log.info(f"GDELT DOC historical: {count} records")
    return count

def collect_ia_conflict_reports():
    """
    Internet Archive — UN reports, SIPRI yearbooks, academic conflict studies.
    Free, no key needed.
    """
    log.info("Collecting conflict reports from Internet Archive...")
    count = 0
    out_path = OUT_DIR / "ia_conflict_reports.jsonl"

    searches = [
        {"q": "UN Security Council Afghanistan report 2021 2022",    "pilot": "afghanistan"},
        {"q": "UNAMA Afghanistan human rights annual report",         "pilot": "afghanistan"},
        {"q": "SIGAR Afghanistan reconstruction quarterly report",    "pilot": "afghanistan"},
        {"q": "SIPRI yearbook armed conflict Afghanistan",            "pilot": "afghanistan"},
        {"q": "Human Rights Watch Afghanistan Taliban 2022",          "pilot": "afghanistan"},
        {"q": "Amnesty International Afghanistan report",             "pilot": "afghanistan"},
        {"q": "UN Security Council Iran nuclear sanctions report",    "pilot": "iran_hormuz"},
        {"q": "IAEA Iran nuclear program verification report",        "pilot": "iran_hormuz"},
        {"q": "ICG Crisis Group Iran conflict analysis",              "pilot": "iran_hormuz"},
        {"q": "SIPRI military expenditure Iran Middle East",          "pilot": "iran_hormuz"},
        {"q": "Human Rights Watch Iran crackdown protest",            "pilot": "iran_hormuz"},
    ]

    for s in searches:
        try:
            resp = requests.get(
                "https://archive.org/advancedsearch.php",
                params={"q": s["q"], "fl[]": "identifier,title,description,date,creator",
                        "rows": 25, "output": "json", "sort[]": "date desc"},
                timeout=20
            )
            if resp.status_code != 200: continue
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                creator = doc.get("creator", "")
                if isinstance(creator, list): creator = "; ".join(creator)
                text = f"{doc.get('title','')}. Creator: {creator}. {desc[:600]}"
                if len(text) < 30: continue
                rec = {
                    "id": hashlib.sha256(doc.get("identifier","").encode()).hexdigest()[:16],
                    "source_name": creator[:60] or doc.get("title","")[:60],
                    "source_url": f"https://archive.org/details/{doc.get('identifier','')}",
                    "source_country": "Multiple",
                    "source_perspective": "UN-NGO-academic-conflict-report",
                    "date": doc.get("date",""),
                    "language": "en",
                    "category": "historical_conflicts",
                    "pilot_conflicts": [s["pilot"]],
                    "conflict_types": [],
                    "text": text,
                    "confidence": "high",
                    "notes": f"IA conflict report search: '{s['q']}'",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"IA conflict report '{s['q'][:40]}': {e}")

    log.info(f"IA conflict reports: {count} records")
    return count


def collect_acled():
    """ACLED — free key at https://developer.acleddata.com — add to .env when ready."""
    if not ACLED_KEY or not ACLED_EMAIL:
        log.info("ACLED: skipped (no key). Register free at https://developer.acleddata.com")
        return 0
    log.info("Collecting ACLED conflict events...")
    count = 0
    out_path = OUT_DIR / "acled_events.jsonl"
    queries = [
        {"country": "Afghanistan", "pilot": "afghanistan", "year": "2018|2019|2020|2021"},
        {"country": "Iran",        "pilot": "iran_hormuz", "year": "2019|2020|2021|2022"},
    ]
    for q in queries:
        try:
            params = {"key": ACLED_KEY, "email": ACLED_EMAIL, "country": q["country"],
                      "year": q["year"], "limit": 2000,
                      "fields": "event_date|event_type|actor1|actor2|country|location|fatalities|notes"}
            resp = requests.get("https://api.acleddata.com/acled/read", params=params, timeout=30)
            if resp.status_code != 200: continue
            for e in resp.json().get("data", []):
                rec = {
                    "id": hashlib.sha256(f"{e.get('event_date','')}_{e.get('location','')}".encode()).hexdigest()[:16],
                    "source_name": "ACLED", "source_url": "https://acleddata.com",
                    "source_country": q["country"], "source_perspective": "Academic-conflict-database",
                    "date": e.get("event_date",""), "language": "en",
                    "category": "historical_conflicts", "pilot_conflicts": [q["pilot"]],
                    "conflict_types": [e.get("event_type","")],
                    "text": f"{e.get('event_type','')} — {e.get('location','')}. {e.get('notes','')[:500]}",
                    "actor1": e.get("actor1",""), "actor2": e.get("actor2",""),
                    "fatalities": e.get("fatalities", 0), "confidence": "high",
                    "notes": "ACLED", "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"ACLED: {e}")
    log.info(f"ACLED: {count} records")
    return count


def run_historical_collection():
    total = 0
    total += collect_gdelt_doc()
    total += collect_ia_conflict_reports()
    total += collect_acled()
    log.info(f"Historical collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_historical_collection()
