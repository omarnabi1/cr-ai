#!/usr/bin/env python3
"""
Ground Truth Collector — CR-AI Expanded Dataset
What populations actually experience vs what governments say.
UNHCR displacement, MSF field reports, ICC atrocity docs,
Arab Barometer surveys, WikiLeaks, Panama Papers financial architecture.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "ground_truth.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "ground_truth"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, cat, pilots, text, conf="medium", notes=""):
    return {
        "id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": sn, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": cat, "pilot_conflicts": pilots, "conflict_types": [],
        "text": text[:3000], "confidence": conf, "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }

def _save(rec, sub):
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def collect_ngo_field_reports():
    """MSF, IRC, Oxfam, HRW, AI — what actually happened on the ground."""
    log.info("Collecting NGO field reports...")
    count = 0
    searches = [
        {"q": "Médecins Sans Frontières MSF Afghanistan field report", "pilot": "afghanistan"},
        {"q": "International Rescue Committee IRC Afghanistan humanitarian", "pilot": "afghanistan"},
        {"q": "Oxfam Afghanistan poverty food security report", "pilot": "afghanistan"},
        {"q": "Human Rights Watch Afghanistan Taliban abuses 2021 2022 2023", "pilot": "afghanistan"},
        {"q": "Amnesty International Afghanistan women rights report", "pilot": "afghanistan"},
        {"q": "MSF Iran medical humanitarian access report", "pilot": "iran_hormuz"},
        {"q": "Human Rights Watch Iran protest crackdown torture prison", "pilot": "iran_hormuz"},
        {"q": "Amnesty International Iran death penalty execution report", "pilot": "iran_hormuz"},
        {"q": "IRC refugee camp conditions Middle East field report", "pilot": "both"},
        {"q": "CARE International gender conflict women Afghanistan Iran", "pilot": "both"},
        {"q": "Save the Children Afghanistan child rights nutrition", "pilot": "afghanistan"},
        {"q": "UNICEF Afghanistan children education malnutrition crisis", "pilot": "afghanistan"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s.get("pilot") == "both" else [s["pilot"]]
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
                _save(_rec(f"NGO Report: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "NGO", "NGO-field-report", doc.get("date",""),
                    "en", "ngo_reports", pilots, text, conf="high",
                    notes=f"NGO: {s['q']}"), "ngo_reports")
                count += 1
        except Exception as e: log.error(f"NGO '{s['q'][:40]}': {e}")
    log.info(f"NGO reports: {count}")
    return count


def collect_atrocity_documentation():
    """
    War crimes, genocide documentation, ICC cases, ICTY precedents.
    The record of what was done and to whom.
    """
    log.info("Collecting atrocity documentation...")
    count = 0
    searches = [
        {"q": "Afghanistan war crimes US military civilian casualties investigation", "pilot": "afghanistan"},
        {"q": "Taliban atrocities Hazara massacre ethnic cleansing documentation", "pilot": "afghanistan"},
        {"q": "Afghanistan ICC investigation war crimes prosecutor report", "pilot": "afghanistan"},
        {"q": "Iran political prisoner execution mass killing 1988", "pilot": "iran_hormuz"},
        {"q": "Iran torture prison Evin human rights documentation", "pilot": "iran_hormuz"},
        {"q": "civilian casualties airstrikes drone Afghanistan documentation", "pilot": "afghanistan"},
        {"q": "sexual violence conflict weapon war Afghanistan", "pilot": "afghanistan"},
        {"q": "forced disappearance enforced disappearance Middle East", "pilot": "both"},
        {"q": "genocide ethnic cleansing documentation prevention", "pilot": "both"},
        {"q": "UNAMA civilian casualty report Afghanistan annual", "pilot": "afghanistan"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s.get("pilot") == "both" else [s["pilot"]]
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
                _save(_rec(f"Atrocity Doc: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Atrocity-war-crimes-documentation", doc.get("date",""),
                    "en", "atrocity_docs", pilots, text, conf="high",
                    notes=f"Atrocity: {s['q']}"), "atrocity_docs")
                count += 1
        except Exception as e: log.error(f"Atrocity '{s['q'][:40]}': {e}")
    log.info(f"Atrocity documentation: {count}")
    return count


def collect_public_opinion_surveys():
    """
    Arab Barometer, Pew, Gallup, local surveys.
    What populations actually believe — not what leaders say they believe.
    """
    log.info("Collecting public opinion survey data...")
    count = 0
    searches = [
        {"q": "Arab Barometer survey Iran public opinion governance", "pilot": "iran_hormuz"},
        {"q": "Pew Research Center Iran public opinion survey", "pilot": "iran_hormuz"},
        {"q": "Gallup Afghanistan public opinion survey governance Taliban", "pilot": "afghanistan"},
        {"q": "Afghan public opinion peace war security survey", "pilot": "afghanistan"},
        {"q": "Iran nuclear program public opinion domestic support", "pilot": "iran_hormuz"},
        {"q": "Middle East public opinion US foreign policy survey", "pilot": "both"},
        {"q": "trust government institution survey conflict country", "pilot": "both"},
        {"q": "women rights education public opinion Afghanistan survey", "pilot": "afghanistan"},
        {"q": "Iran youth generational change attitude survey", "pilot": "iran_hormuz"},
        {"q": "conflict fatigue civilian population peace desire survey", "pilot": "both"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s.get("pilot") == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date",
                "rows": 15, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Survey: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Public-opinion-survey", doc.get("date",""),
                    "en", "public_opinion", pilots, text,
                    notes=f"Survey: {s['q']}"), "public_opinion")
                count += 1
        except Exception as e: log.error(f"Survey '{s['q'][:40]}': {e}")
    log.info(f"Public opinion: {count}")
    return count


def collect_leaks_financial():
    """
    WikiLeaks Afghan War Diary, Iran cables, Panama Papers.
    The financial architecture underneath conflicts.
    Follow the money to find the real interests.
    """
    log.info("Collecting leaks and financial architecture data...")
    count = 0
    searches = [
        {"q": "WikiLeaks Afghan War Diary classified cables 2010", "pilot": "afghanistan"},
        {"q": "WikiLeaks State Department cables Iran diplomatic secret", "pilot": "iran_hormuz"},
        {"q": "Panama Papers Iran offshore accounts sanctions evasion", "pilot": "iran_hormuz"},
        {"q": "IRGC financial empire business network Iran economy", "pilot": "iran_hormuz"},
        {"q": "corruption Afghanistan reconstruction funds theft", "pilot": "afghanistan"},
        {"q": "Taliban financial network hawala remittance opium revenue", "pilot": "afghanistan"},
        {"q": "Iran sanctions evasion shell companies money laundering", "pilot": "iran_hormuz"},
        {"q": "war profiteering contractor fraud Afghanistan reconstruction", "pilot": "afghanistan"},
        {"q": "offshore accounts dictator oligarch Middle East financial", "pilot": "both"},
        {"q": "Pandora Papers Afghanistan Iran elite financial secrets", "pilot": "both"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s.get("pilot") == "both" else [s["pilot"]]
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
                _save(_rec(f"Leaks/Financial: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Leaks-financial-architecture", doc.get("date",""),
                    "en", "leaks_financial", pilots, text,
                    notes=f"Leaks: {s['q']}"), "leaks_financial")
                count += 1
        except Exception as e: log.error(f"Leaks '{s['q'][:40]}': {e}")
    log.info(f"Leaks/financial: {count}")
    return count


def run_ground_truth():
    total = 0
    total += collect_ngo_field_reports()
    total += collect_atrocity_documentation()
    total += collect_public_opinion_surveys()
    total += collect_leaks_financial()
    log.info(f"Ground truth complete: {total} records")
    return total

if __name__ == "__main__":
    run_ground_truth()
