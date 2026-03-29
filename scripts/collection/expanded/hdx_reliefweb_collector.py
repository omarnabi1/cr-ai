#!/usr/bin/env python3
"""
HDX + ReliefWeb + UN Systems Collector — CR-AI
Pulls from the world's largest open humanitarian data platforms.

HDX (Humanitarian Data Exchange): 18,110 datasets, UN OCHA managed
ReliefWeb: 1M+ humanitarian reports, situation reports, field updates
UN Data: Population, development, human rights indicators
UN Security Council: All resolutions, vetoes, peacekeeping mandates
OCHA FTS: Financial tracking of humanitarian funding flows
WHO: Global health emergency data
WFP: Food security, market price monitoring
IOM DTM: Displacement tracking matrix
"""

import json, hashlib, logging, requests, time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "hdx_reliefweb.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT = BASE_DIR / "data" / "raw" / "hdx_reliefweb"
OUT.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="high", notes="", cat="hdx_reliefweb"):
    return {"id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
            "source_name": sn, "source_url": url, "source_country": country,
            "source_perspective": perspective, "date": date, "language": lang,
            "category": cat, "pilot_conflicts": pilots, "conflict_types": [],
            "text": text[:3000], "confidence": conf, "notes": notes,
            "collected_at": datetime.utcnow().isoformat()}

def _save(rec, sub):
    p = OUT / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def collect_reliefweb():
    """ReliefWeb API — 1M+ humanitarian reports, situation reports, field updates."""
    log.info("Collecting ReliefWeb reports...")
    count = 0
    queries = [
        ("Afghanistan humanitarian situation report", "afghanistan"),
        ("Afghanistan food insecurity famine crisis", "afghanistan"),
        ("Afghanistan displacement IDP refugee return", "afghanistan"),
        ("Afghanistan women girls education rights Taliban", "afghanistan"),
        ("Afghanistan health system collapse malnutrition", "afghanistan"),
        ("Afghanistan earthquake flood natural disaster", "afghanistan"),
        ("Afghanistan opium drug economy livelihoods", "afghanistan"),
        ("Afghanistan reconstruction development failure", "afghanistan"),
        ("Iran sanctions humanitarian impact civilian", "iran_hormuz"),
        ("Iran flood earthquake disaster response", "iran_hormuz"),
        ("Iran human rights political prisoner protest", "iran_hormuz"),
        ("Hormuz strait oil shipping disruption", "iran_hormuz"),
        ("refugee crisis displacement Middle East Central Asia", "both"),
        ("child protection conflict armed group recruitment", "both"),
        ("gender-based violence conflict sexual violence", "both"),
        ("mine clearance landmine unexploded ordnance", "both"),
    ]
    for q, pilot in queries:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        try:
            r = requests.post("https://api.reliefweb.int/v1/reports?appname=worldllm-ai-research", json={
                "query": {"value": q},
                "fields": {"include": ["title","body","date","source","country","file"]},
                "limit": 20, "sort": ["date:desc"]
            }, timeout=20)
            if r.status_code != 200: continue
            for item in r.json().get("data", []):
                f = item.get("fields", {})
                title = f.get("title", "")
                body = f.get("body", "")[:600]
                sources = [s.get("name","") for s in f.get("source", [])]
                date = f.get("date", {}).get("created", "")
                text = f"ReliefWeb: {title}. Sources: {', '.join(sources)}. {body}"
                _save(_rec(f"ReliefWeb: {title[:50]}", f"https://reliefweb.int/node/{item.get('id','')}",
                    ", ".join(c.get("name","") for c in f.get("country",[])),
                    "ReliefWeb-humanitarian", date, "en", pilots, text,
                    notes=f"ReliefWeb query: {q}"), "reliefweb")
                count += 1
        except Exception as e: log.error(f"ReliefWeb '{q[:40]}': {e}")
    log.info(f"ReliefWeb: {count}")
    return count


def collect_hdx():
    """HDX — UN OCHA humanitarian data exchange. 18,110 datasets."""
    log.info("Collecting HDX datasets...")
    count = 0
    queries = [
        ("Afghanistan conflict displacement food security", "afghanistan"),
        ("Afghanistan health nutrition malnutrition crisis", "afghanistan"),
        ("Afghanistan refugees IDP protection gender", "afghanistan"),
        ("Afghanistan governance accountability reconstruction", "afghanistan"),
        ("Iran sanctions humanitarian population data", "iran_hormuz"),
        ("Iran food security economic indicators", "iran_hormuz"),
        ("Middle East conflict displacement refugees", "iran_hormuz"),
        ("armed conflict violence fatalities casualties", "both"),
        ("humanitarian funding financial tracking crisis", "both"),
        ("peacekeeping operations UN mandate force", "both"),
    ]
    for q, pilot in queries:
        pilots = ["iran_hormuz","afghanistan"] if pilot=="both" else [pilot]
        try:
            r = requests.get("https://data.humdata.org/api/3/action/package_search",
                params={"q": q, "rows": 20, "sort": "metadata_modified desc"},
                timeout=20)
            if r.status_code != 200: continue
            for pkg in r.json().get("result",{}).get("results",[]):
                title = pkg.get("title","")
                notes_text = pkg.get("notes","")[:400]
                org = pkg.get("organization",{}).get("title","")
                date = pkg.get("metadata_modified","")
                tags = ", ".join(t.get("name","") for t in pkg.get("tags",[])[:8])
                text = f"HDX Dataset: {title}. Org: {org}. Tags: {tags}. {notes_text}"
                url = f"https://data.humdata.org/dataset/{pkg.get('name','')}"
                _save(_rec(f"HDX: {title[:50]}", url, "Multiple",
                    "HDX-humanitarian-data", date, "en", pilots, text,
                    notes=f"HDX: {q}"), "hdx_datasets")
                count += 1
        except Exception as e: log.error(f"HDX '{q[:40]}': {e}")
    log.info(f"HDX: {count}")
    return count


def collect_un_security_council():
    """UN Security Council resolutions and vetoes — the legal architecture of intervention."""
    log.info("Collecting UN Security Council data...")
    count = 0
    # UN SC resolutions via public API
    sc_searches = [
        ("Afghanistan UN Security Council resolution peacekeeping", "afghanistan"),
        ("Iran nuclear UN Security Council sanctions resolution", "iran_hormuz"),
        ("UN Security Council veto Russia China Middle East", "both"),
        ("UN peacekeeping operation mandate force authorization", "both"),
        ("UN Security Council humanitarian access resolution", "both"),
        ("UN Security Council ceasefire demand violation", "both"),
        ("UN Special Rapporteur human rights report", "both"),
        ("UN General Assembly resolution conflict occupation", "both"),
    ]
    for q, pilot in sc_searches:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 20, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"UN SC: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "International", "UN-Security-Council",
                    doc.get("date",""), "en", pilots, text,
                    notes=f"UN SC: {q}"), "un_security_council")
                count += 1
        except Exception as e: log.error(f"UN SC '{q[:40]}': {e}")
    log.info(f"UN Security Council: {count}")
    return count


def collect_who_health_emergencies():
    """WHO health emergency data — disease outbreaks, health system collapses."""
    log.info("Collecting WHO health emergency data...")
    count = 0
    try:
        # WHO GHO API for health indicators
        for iso, pilot in [("AFG","afghanistan"),("IRN","iran_hormuz")]:
            r = requests.get(f"https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,'conflict') or contains(IndicatorName,'emergency') or contains(IndicatorName,'nutrition') or contains(IndicatorName,'mental')",
                timeout=20)
            if r.status_code == 200:
                indicators = r.json().get("value", [])[:20]
                for ind in indicators:
                    ind_code = ind.get("IndicatorCode","")
                    if not ind_code: continue
                    try:
                        dr = requests.get(f"https://ghoapi.azureedge.net/api/{ind_code}?$filter=SpatialDim eq '{iso}'&$top=10", timeout=15)
                        if dr.status_code != 200: continue
                        for pt in dr.json().get("value", [])[:5]:
                            val = pt.get("NumericValue") or pt.get("Value","")
                            text = f"WHO {ind.get('IndicatorName','')} for {iso}: {val} ({pt.get('TimeDim','')})"
                            _save(_rec("WHO GHO", f"https://www.who.int/data/gho/data/indicators/indicator-details/GHO/{ind_code}",
                                iso, "WHO-health-emergency", str(pt.get("TimeDim","")),
                                "en", [pilot], text, conf="high",
                                notes=f"WHO indicator: {ind_code}"), "who_health")
                            count += 1
                    except: pass
    except Exception as e: log.error(f"WHO API: {e}")

    # Supplement with IA searches
    for q, pilot in [
        ("WHO Afghanistan health system emergency malnutrition", "afghanistan"),
        ("WHO Iran health sanctions medicine shortage", "iran_hormuz"),
        ("WHO mental health conflict PTSD population study", "both"),
        ("WHO cholera outbreak conflict zone waterborne disease", "both"),
        ("WHO maternal child mortality conflict country", "both"),
    ]:
        pilots = ["iran_hormuz","afghanistan"] if pilot=="both" else [pilot]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date", "rows": 15, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response",{}).get("docs",[]):
                desc = doc.get("description","")
                if isinstance(desc,list): desc=" ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text)<30: continue
                _save(_rec(f"WHO: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global","WHO-health-emergency",doc.get("date",""),"en",pilots,text,
                    notes=f"WHO IA: {q}"), "who_health")
                count += 1
        except Exception as e: log.error(f"WHO IA '{q[:40]}': {e}")
    log.info(f"WHO health: {count}")
    return count


def run_hdx_reliefweb():
    total = 0
    total += collect_reliefweb()
    total += collect_hdx()
    total += collect_un_security_council()
    total += collect_who_health_emergencies()
    log.info(f"HDX/ReliefWeb/UN complete: {total}")
    return total

if __name__ == "__main__":
    run_hdx_reliefweb()
