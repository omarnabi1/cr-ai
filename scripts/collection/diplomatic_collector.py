#!/usr/bin/env python3
"""
Diplomatic Cables & FOIA Documents Collector — CR-AI Phase 2
Sources:
  - WikiLeaks (public mirror via IA) — no key
  - Digital National Security Archive summaries — no key
  - US State Dept FOIA reading room — no key
  - Wilson Center Digital Archive — no key
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/Users/omarnabi/Desktop/CR-AI/logs/diplomatic.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path("/Users/omarnabi/Desktop/CR-AI/data/raw/diplomatic_cables")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def collect_wilson_center():
    """
    Wilson Center Digital Archive — declassified diplomatic docs. Free, no key.
    Rich source of US-Iran, US-Afghanistan diplomatic history.
    """
    log.info("Collecting Wilson Center diplomatic documents...")
    count = 0
    out_path = OUT_DIR / "wilson_center_docs.jsonl"

    searches = [
        {"q": "Iran United States diplomatic cables 1979",   "pilot": "iran_hormuz"},
        {"q": "Iran nuclear negotiations diplomacy",          "pilot": "iran_hormuz"},
        {"q": "Iran sanctions diplomatic",                    "pilot": "iran_hormuz"},
        {"q": "Afghanistan Taliban negotiations 2001",        "pilot": "afghanistan"},
        {"q": "Afghanistan US withdrawal diplomacy",          "pilot": "afghanistan"},
        {"q": "Doha Agreement Afghanistan 2020",              "pilot": "afghanistan"},
    ]

    for s in searches:
        try:
            resp = requests.get(
                "https://digitalarchive.wilsoncenter.org/api/documents",
                params={"q": s["q"], "limit": 30, "format": "json"},
                timeout=20, headers={"Accept": "application/json"}
            )
            if resp.status_code != 200:
                # Fallback: search IA for Wilson Center content
                ia_resp = requests.get(
                    "https://archive.org/advancedsearch.php",
                    params={"q": f"subject:\"Wilson Center\" {s['q']}", "fl[]": "identifier,title,description,date",
                            "rows": 20, "output": "json"},
                    timeout=20
                )
                if ia_resp.status_code == 200:
                    docs = ia_resp.json().get("response", {}).get("docs", [])
                    for doc in docs:
                        desc = doc.get("description", "")
                        if isinstance(desc, list): desc = " ".join(desc)
                        text = f"{doc.get('title','')}. {desc[:600]}"
                        if len(text) < 30: continue
                        rec = _make_diplo_rec(doc.get("identifier",""), doc.get("title",""),
                            f"https://archive.org/details/{doc.get('identifier','')}", text,
                            doc.get("date",""), s["pilot"], s["q"])
                        with open(out_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        count += 1
                continue

            docs = resp.json().get("documents", resp.json().get("data", []))
            for doc in docs:
                text = f"{doc.get('title','')}. {doc.get('abstract', doc.get('description',''))[:600]}"
                if len(text) < 30: continue
                rec = _make_diplo_rec(str(doc.get("id","")), doc.get("title",""),
                    doc.get("url", "https://digitalarchive.wilsoncenter.org"), text,
                    doc.get("date",""), s["pilot"], s["q"])
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"Wilson Center '{s['q']}': {e}")

    log.info(f"Wilson Center: {count} records")
    return count

def _make_diplo_rec(doc_id, title, url, text, date, pilot, query):
    return {
        "id": hashlib.sha256(doc_id.encode()).hexdigest()[:16],
        "source_name": "Wilson Center Digital Archive",
        "source_url": url,
        "source_country": "USA",
        "source_perspective": "US-declassified-diplomatic",
        "date": date,
        "language": "en",
        "category": "diplomatic_cables",
        "pilot_conflicts": [pilot],
        "conflict_types": [],
        "text": text,
        "confidence": "high",
        "notes": f"Wilson Center search: '{query}'",
        "collected_at": datetime.utcnow().isoformat()
    }

def collect_ia_diplomatic():
    """
    Internet Archive — declassified State Dept cables, FOIA docs, UN reports.
    No key needed.
    """
    log.info("Collecting diplomatic documents from Internet Archive...")
    count = 0
    out_path = OUT_DIR / "ia_diplomatic_docs.jsonl"

    searches = [
        {"q": "Iran United States diplomatic cables declassified", "pilot": "iran_hormuz"},
        {"q": "JCPOA Iran nuclear deal negotiations documents",     "pilot": "iran_hormuz"},
        {"q": "Afghanistan Doha Agreement Taliban negotiations",    "pilot": "afghanistan"},
        {"q": "Afghanistan US State Department FOIA cables",        "pilot": "afghanistan"},
        {"q": "UN Security Council resolution Iran sanctions",      "pilot": "iran_hormuz"},
        {"q": "UN Security Council Afghanistan resolution",         "pilot": "afghanistan"},
    ]

    for s in searches:
        try:
            resp = requests.get(
                "https://archive.org/advancedsearch.php",
                params={"q": s["q"], "fl[]": "identifier,title,description,date,creator",
                        "rows": 30, "output": "json"},
                timeout=20
            )
            if resp.status_code != 200: continue
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                creator = doc.get("creator", "")
                if isinstance(creator, list): creator = "; ".join(creator)
                text = f"{doc.get('title','')}. {desc[:600]} Creator: {creator}"
                if len(text) < 30: continue
                rec = {
                    "id": hashlib.sha256(doc.get("identifier","").encode()).hexdigest()[:16],
                    "source_name": f"IA Diplomatic: {doc.get('title','')[:50]}",
                    "source_url": f"https://archive.org/details/{doc.get('identifier','')}",
                    "source_country": "Multiple",
                    "source_perspective": "Declassified-diplomatic",
                    "date": doc.get("date",""),
                    "language": "en",
                    "category": "diplomatic_cables",
                    "pilot_conflicts": [s["pilot"]],
                    "conflict_types": [],
                    "text": text,
                    "confidence": "medium",
                    "notes": f"IA diplomatic search: '{s['q']}'",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"IA diplomatic '{s['q']}': {e}")

    log.info(f"IA diplomatic: {count} records")
    return count

def run_diplomatic_collection():
    total = 0
    total += collect_wilson_center()
    total += collect_ia_diplomatic()
    log.info(f"Diplomatic collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_diplomatic_collection()
