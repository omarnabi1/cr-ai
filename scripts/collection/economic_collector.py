#!/usr/bin/env python3
"""
Economic Incentives & Illicit Economy Collector — CR-AI Phase 2
Sources:
  - World Bank Open Data API (free, no key)
  - IMF World Economic Outlook (free)
  - UNODC drug reports (Internet Archive)
  - Global Financial Integrity reports (IA)
  - SIPRI military expenditure (free API)
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/Users/omarnabi/Desktop/CR-AI/logs/economic.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

ECON_DIR  = Path("/Users/omarnabi/Desktop/CR-AI/data/raw/economic_incentives")
ILLICIT_DIR = Path("/Users/omarnabi/Desktop/CR-AI/data/raw/illicit_economy")
MINERALS_DIR = Path("/Users/omarnabi/Desktop/CR-AI/data/raw/minerals")
for d in [ECON_DIR, ILLICIT_DIR, MINERALS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# World Bank country codes
WB_COUNTRIES = {"afghanistan": "AFG", "iran_hormuz": "IRN"}

# Key economic indicators for conflict analysis
WB_INDICATORS = [
    ("NY.GDP.MKTP.CD",   "GDP_current_USD"),
    ("NY.GDP.PCAP.CD",   "GDP_per_capita_USD"),
    ("FP.CPI.TOTL.ZG",  "inflation_rate"),
    ("SL.UEM.TOTL.ZS",  "unemployment_rate"),
    ("SP.POP.TOTL",      "population"),
    ("MS.MIL.XPND.GD.ZS","military_expenditure_pct_GDP"),
    ("IC.REG.COST.PC.FE.ZS", "business_registration_cost"),
]

def collect_world_bank():
    """World Bank Open Data — free, no key needed."""
    log.info("Collecting World Bank economic indicators...")
    count = 0
    out_path = ECON_DIR / "world_bank_indicators.jsonl"

    for pilot, iso in WB_COUNTRIES.items():
        for indicator_code, indicator_name in WB_INDICATORS:
            try:
                resp = requests.get(
                    f"https://api.worldbank.org/v2/country/{iso}/indicator/{indicator_code}",
                    params={"format": "json", "per_page": 20, "mrv": 20},
                    timeout=15
                )
                if resp.status_code != 200: continue
                data = resp.json()
                if len(data) < 2: continue
                records = data[1] or []
                for r in records:
                    if r.get("value") is None: continue
                    text = f"{indicator_name} for {iso}: {r.get('value')} ({r.get('date','')})"
                    rec = {
                        "id": hashlib.sha256(f"{iso}_{indicator_code}_{r.get('date','')}".encode()).hexdigest()[:16],
                        "source_name": "World Bank Open Data",
                        "source_url": f"https://data.worldbank.org/indicator/{indicator_code}?locations={iso}",
                        "source_country": iso,
                        "source_perspective": "International-economic-data",
                        "date": r.get("date", ""),
                        "language": "en",
                        "category": "economic_incentives",
                        "pilot_conflicts": [pilot],
                        "conflict_types": [],
                        "text": text,
                        "indicator": indicator_code,
                        "indicator_name": indicator_name,
                        "value": r.get("value"),
                        "confidence": "high",
                        "notes": "World Bank Open Data API",
                        "collected_at": datetime.utcnow().isoformat()
                    }
                    with open(out_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
            except Exception as e:
                log.error(f"World Bank {iso}/{indicator_code}: {e}")

    log.info(f"World Bank: {count} records")
    return count

def collect_illicit_economy():
    """
    UNODC and Global Financial Integrity reports on illicit economy.
    Afghanistan opium trade, Iran sanctions evasion — key conflict drivers.
    """
    log.info("Collecting illicit economy data from Internet Archive...")
    count = 0
    out_path = ILLICIT_DIR / "illicit_economy_reports.jsonl"

    searches = [
        {"q": "Afghanistan opium drug trade UNODC report",      "pilot": "afghanistan"},
        {"q": "Afghanistan Taliban drug revenue financing",       "pilot": "afghanistan"},
        {"q": "Iran sanctions evasion illicit finance",          "pilot": "iran_hormuz"},
        {"q": "Iran oil smuggling sanctions violations",         "pilot": "iran_hormuz"},
        {"q": "Afghanistan mineral resources conflict financing", "pilot": "afghanistan"},
        {"q": "hawala informal money transfer Afghanistan Iran",  "pilot": "both"},
    ]

    for s in searches:
        try:
            resp = requests.get(
                "https://archive.org/advancedsearch.php",
                params={"q": s["q"], "fl[]": "identifier,title,description,date", "rows": 20, "output": "json"},
                timeout=20
            )
            if resp.status_code != 200: continue
            docs = resp.json().get("response", {}).get("docs", [])
            pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
            for doc in docs:
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                rec = {
                    "id": hashlib.sha256(doc.get("identifier","").encode()).hexdigest()[:16],
                    "source_name": f"IA: {doc.get('title','')[:50]}",
                    "source_url": f"https://archive.org/details/{doc.get('identifier','')}",
                    "source_country": "Multiple",
                    "source_perspective": "UNODC-illicit-economy",
                    "date": doc.get("date",""),
                    "language": "en",
                    "category": "illicit_economy",
                    "pilot_conflicts": pilots,
                    "conflict_types": ["illicit_economy"],
                    "text": text,
                    "confidence": "medium",
                    "notes": f"Illicit economy search: '{s['q']}'",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"Illicit economy '{s['q']}': {e}")

    log.info(f"Illicit economy: {count} records")
    return count

def collect_minerals():
    """Afghanistan mineral resources — key economic driver and conflict incentive."""
    log.info("Collecting minerals/natural resources data...")
    count = 0
    out_path = MINERALS_DIR / "minerals_resources.jsonl"

    searches = [
        "Afghanistan lithium mineral resources conflict",
        "Afghanistan rare earth minerals Taliban",
        "Afghanistan copper iron ore mining Aynak",
        "Iran oil natural gas reserves Hormuz",
        "Iran petrochemical industry sanctions",
    ]

    for q in searches:
        pilot = "afghanistan" if "Afghanistan" in q else "iran_hormuz"
        try:
            resp = requests.get(
                "https://archive.org/advancedsearch.php",
                params={"q": q, "fl[]": "identifier,title,description,date", "rows": 15, "output": "json"},
                timeout=20
            )
            if resp.status_code != 200: continue
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                rec = {
                    "id": hashlib.sha256(doc.get("identifier","").encode()).hexdigest()[:16],
                    "source_name": f"IA: {doc.get('title','')[:50]}",
                    "source_url": f"https://archive.org/details/{doc.get('identifier','')}",
                    "source_country": "AFG" if pilot == "afghanistan" else "IRN",
                    "source_perspective": "Natural-resources-data",
                    "date": doc.get("date",""),
                    "language": "en",
                    "category": "minerals",
                    "pilot_conflicts": [pilot],
                    "conflict_types": ["resource_conflict"],
                    "text": text,
                    "confidence": "medium",
                    "notes": f"Minerals search: '{q}'",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"Minerals '{q}': {e}")

    log.info(f"Minerals: {count} records")
    return count

def run_economic_collection():
    total = 0
    total += collect_world_bank()
    total += collect_illicit_economy()
    total += collect_minerals()
    log.info(f"Economic collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_economic_collection()
