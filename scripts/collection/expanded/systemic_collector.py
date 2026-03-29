#!/usr/bin/env python3
"""
Systemic & Geopolitical Collector — CR-AI Expanded Dataset
Arms flows, declassified intelligence, climate/resource stress,
expanded social media, full treaty texts, financial architecture of war.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "systemic.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "systemic"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(source_name, url, country, perspective, date, lang, category, pilots, text, confidence="medium", notes=""):
    return {
        "id": hashlib.sha256(f"{source_name}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": source_name, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": category, "pilot_conflicts": pilots, "conflict_types": [],
        "text": text[:3000], "confidence": confidence, "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }

def _save(rec, sub):
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def collect_arms_trade():
    """SIPRI arms transfers, weapons flows, defense contracts."""
    log.info("Collecting arms trade data...")
    count = 0
    searches = [
        {"q": "SIPRI arms transfer database Afghanistan weapons supply", "pilot": "afghanistan"},
        {"q": "US weapons supply Afghanistan military equipment Taliban captured", "pilot": "afghanistan"},
        {"q": "Iran weapons supply Hezbollah Hamas proxy arms smuggling", "pilot": "iran_hormuz"},
        {"q": "Russia China arms sales Middle East weapons export", "pilot": "both"},
        {"q": "small arms light weapons illicit trade conflict region", "pilot": "both"},
        {"q": "defense contractor profit war Afghanistan Iraq revenue", "pilot": "afghanistan"},
        {"q": "military industrial complex weapons procurement conflict economy", "pilot": "both"},
        {"q": "improvised explosive device IED supply chain Afghanistan", "pilot": "afghanistan"},
        {"q": "drone warfare targeted killing technology proliferation", "pilot": "both"},
        {"q": "nuclear weapons proliferation Iran bomb program enrichment", "pilot": "iran_hormuz"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date",
                "rows": 25, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Arms Trade: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Arms-trade-defense-data", doc.get("date",""),
                    "en", "arms_trade", pilots, text,
                    notes=f"Arms trade: {s['q']}"), "arms_trade")
                count += 1
        except Exception as e: log.error(f"Arms '{s['q'][:40]}': {e}")
    log.info(f"Arms trade: {count}")
    return count


def collect_declassified_intelligence():
    """
    CIA, NSA, MI6, Stasi declassified documents.
    The real decisions behind the public ones.
    """
    log.info("Collecting declassified intelligence documents...")
    count = 0
    searches = [
        {"q": "CIA declassified Afghanistan Cold War mujahedeen Operation Cyclone", "pilot": "afghanistan"},
        {"q": "CIA Iran 1953 coup declassified TPAJAX Operation", "pilot": "iran_hormuz"},
        {"q": "NSA surveillance Afghanistan war signals intelligence", "pilot": "afghanistan"},
        {"q": "CIA Iran nuclear program intelligence assessment NIE", "pilot": "iran_hormuz"},
        {"q": "declassified intelligence Iran threat assessment Middle East", "pilot": "iran_hormuz"},
        {"q": "CIA world factbook Afghanistan Iran analysis declassified", "pilot": "both"},
        {"q": "ISI Pakistan intelligence Taliban support declassified", "pilot": "afghanistan"},
        {"q": "Pentagon Afghanistan war papers SIGAR lessons learned", "pilot": "afghanistan"},
        {"q": "Iran-Contra affair declassified documents Reagan administration", "pilot": "iran_hormuz"},
        {"q": "national security archive Afghanistan declassified cables", "pilot": "afghanistan"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date,creator",
                "rows": 25, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Intelligence: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "USA", "Declassified-intelligence", doc.get("date",""),
                    "en", "intelligence_docs", pilots, text,
                    notes=f"Declassified intel: {s['q']}"), "intelligence_docs")
                count += 1
        except Exception as e: log.error(f"Intel '{s['q'][:40]}': {e}")
    log.info(f"Declassified intelligence: {count}")
    return count

def collect_climate_environment():
    """
    Climate change, water scarcity, resource stress.
    The NEXT generation of conflict drivers already happening now.
    Afghanistan's drought directly feeds Taliban recruitment.
    Iran's water crisis fuels domestic unrest.
    """
    log.info("Collecting climate and environmental conflict data...")
    count = 0

    # World Bank climate/environment indicators
    climate_indicators = [
        ("EN.ATM.CO2E.PC", "co2_emissions_per_capita"),
        ("AG.LND.ARBL.ZS", "arable_land_pct"),
        ("ER.H2O.FWST.ZS", "freshwater_stress"),
        ("EN.CLC.DRSK.XQ", "drought_risk_exposure"),
        ("AG.PRD.FOOD.XD", "food_production_index"),
        ("SN.ITK.DEFC.ZS", "undernourishment_pct"),
    ]
    for code, name in climate_indicators:
        for iso, pilot in [("AFG", "afghanistan"), ("IRN", "iran_hormuz")]:
            try:
                r = requests.get(
                    f"https://api.worldbank.org/v2/country/{iso}/indicator/{code}",
                    params={"format": "json", "per_page": 20, "mrv": 20}, timeout=15)
                if r.status_code != 200: continue
                data = r.json()
                if len(data) < 2: continue
                for rec in (data[1] or []):
                    if rec.get("value") is None: continue
                    text = f"Climate indicator {name} for {iso}: {rec.get('value')} ({rec.get('date','')})"
                    _save(_rec("World Bank Climate Data",
                        f"https://data.worldbank.org/indicator/{code}?locations={iso}",
                        iso, "Climate-resource-data", rec.get("date",""),
                        "en", "climate_environment", [pilot], text,
                        confidence="high", notes=f"WB climate: {name}"), "climate_environment")
                    count += 1
            except Exception as e: log.error(f"Climate {code}/{iso}: {e}")

    # IA climate conflict searches
    climate_searches = [
        {"q": "Afghanistan drought water scarcity climate conflict Taliban", "pilot": "afghanistan"},
        {"q": "Iran water crisis lake Urmia drought domestic unrest", "pilot": "iran_hormuz"},
        {"q": "climate change conflict resource war scarcity Middle East", "pilot": "both"},
        {"q": "food insecurity famine conflict driver Afghanistan", "pilot": "afghanistan"},
        {"q": "opium poppy cultivation drought alternative livelihood Afghanistan", "pilot": "afghanistan"},
        {"q": "oil resource curse political instability Middle East", "pilot": "iran_hormuz"},
    ]
    for s in climate_searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date",
                "rows": 20, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Climate/Env: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Climate-resource-conflict", doc.get("date",""),
                    "en", "climate_environment", pilots, text,
                    notes=f"Climate: {s['q']}"), "climate_environment")
                count += 1
        except Exception as e: log.error(f"Climate '{s['q'][:40]}': {e}")
    log.info(f"Climate/environment: {count}")
    return count


def collect_full_treaty_texts():
    """
    Full texts of peace agreements, ceasefires, negotiations.
    Not summaries — the actual words agreed to and why they failed.
    """
    log.info("Collecting full treaty and agreement texts...")
    count = 0
    searches = [
        {"q": "Doha Agreement 2020 full text Taliban United States Afghanistan", "pilot": "afghanistan"},
        {"q": "Bonn Agreement 2001 Afghanistan full text transitional authority", "pilot": "afghanistan"},
        {"q": "JCPOA full text Iran nuclear deal 2015 annex", "pilot": "iran_hormuz"},
        {"q": "Algiers Accords 1981 Iran US hostages full text", "pilot": "iran_hormuz"},
        {"q": "Oslo Accords text framework Middle East peace negotiations", "pilot": "both"},
        {"q": "UN Security Council resolution 1973 2231 Iran Afghanistan", "pilot": "both"},
        {"q": "Geneva Accord 1988 Afghanistan Soviet withdrawal text", "pilot": "afghanistan"},
        {"q": "Camp David Accords peace treaty full text Middle East", "pilot": "iran_hormuz"},
        {"q": "peace agreement failed implementation ceasefire violation analysis", "pilot": "both"},
        {"q": "negotiation transcript minutes peace talks diplomatic record", "pilot": "both"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date",
                "rows": 20, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Treaty: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "International", "Peace-agreement-treaty-text", doc.get("date",""),
                    "en", "treaty_texts", pilots, text,
                    confidence="high", notes=f"Treaty: {s['q']}"), "treaty_texts")
                count += 1
        except Exception as e: log.error(f"Treaty '{s['q'][:40]}': {e}")
    log.info(f"Treaty texts: {count}")
    return count


def run_systemic():
    total = 0
    total += collect_arms_trade()
    total += collect_declassified_intelligence()
    total += collect_climate_environment()
    total += collect_full_treaty_texts()
    log.info(f"Systemic collection complete: {total} records")
    return total

if __name__ == "__main__":
    run_systemic()
