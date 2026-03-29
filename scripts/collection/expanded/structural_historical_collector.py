#!/usr/bin/env python3
"""
Structural & Historical Collector — CR-AI Expanded Dataset
The deep roots layer: colonial history, international law, all religious traditions,
demographic data, and academic conflict studies.

You cannot do root cause analysis without the root. These are the roots.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "structural_historical.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "structural_historical"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(source_name, url, country, perspective, date, lang, category, pilots, text, confidence="high", notes=""):
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


def collect_colonial_history():
    """
    Colonial border drawing, mandate papers, Great Game documents.
    The Durand Line (1893) still drives Taliban strategy today.
    Sykes-Picot (1916) still drives Middle East instability.
    """
    log.info("Collecting colonial history...")
    count = 0
    searches = [
        {"q": "Durand Line Afghanistan Pakistan border 1893 British colonial", "pilot": "afghanistan"},
        {"q": "Great Game British Russia Afghanistan 19th century imperial", "pilot": "afghanistan"},
        {"q": "Anglo-Afghan wars British colonial history", "pilot": "afghanistan"},
        {"q": "British India partition border colonial legacy conflict", "pilot": "afghanistan"},
        {"q": "Sykes-Picot agreement 1916 Middle East borders colonial", "pilot": "iran_hormuz"},
        {"q": "British Mandate Iran Persia colonial oil Anglo-Iranian", "pilot": "iran_hormuz"},
        {"q": "1953 Iran coup Mossadegh CIA MI6 regime change", "pilot": "iran_hormuz"},
        {"q": "Ottoman Empire collapse successor states Middle East legacy", "pilot": "iran_hormuz"},
        {"q": "colonial legacy ethnic conflict arbitrary borders Africa Asia", "pilot": "both"},
        {"q": "imperial power proxy war Cold War Afghanistan Iran", "pilot": "both"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date,creator",
                "rows": 30, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Colonial History: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Colonial-historical-record", doc.get("date",""),
                    "en", "colonial_history", pilots, text,
                    notes=f"Colonial history: {s['q']}"), "colonial_history")
                count += 1
        except Exception as e: log.error(f"Colonial '{s['q'][:40]}': {e}")
    log.info(f"Colonial history: {count}")
    return count


def collect_international_law():
    """
    ICJ rulings, Geneva Conventions, war crimes law, UN Charter.
    What the international system TRIED to do — and why it failed.
    """
    log.info("Collecting international law corpus...")
    count = 0
    searches = [
        {"q": "International Court Justice ICJ ruling Middle East conflict", "pilot": "both"},
        {"q": "Geneva Conventions war crimes laws armed conflict", "pilot": "both"},
        {"q": "ICC International Criminal Court Afghanistan war crimes", "pilot": "afghanistan"},
        {"q": "UN Charter Chapter 6 7 peace security enforcement", "pilot": "both"},
        {"q": "responsibility to protect R2P humanitarian intervention", "pilot": "both"},
        {"q": "nuclear non-proliferation treaty NPT Iran IAEA", "pilot": "iran_hormuz"},
        {"q": "sanctions international law legality economic warfare", "pilot": "iran_hormuz"},
        {"q": "laws of war civilian protection proportionality Afghanistan", "pilot": "afghanistan"},
        {"q": "international humanitarian law IHL occupation Taliban", "pilot": "afghanistan"},
        {"q": "self-determination independence sovereignty international law", "pilot": "both"},
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
                _save(_rec(f"Intl Law: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "International", "International-legal-framework", doc.get("date",""),
                    "en", "international_law", pilots, text,
                    notes=f"Intl law: {s['q']}"), "international_law")
                count += 1
        except Exception as e: log.error(f"Intl law '{s['q'][:40]}': {e}")
    log.info(f"International law: {count}")
    return count

def collect_all_religious_traditions():
    """
    ALL major religious texts and traditions — not just Islamic.
    The Bible shaped Crusader logic still referenced today.
    The Torah shapes Israeli policy debates.
    Hindu nationalism shapes Pakistan/India proxy dynamics in Afghanistan.
    Buddhist non-violence principles inform resolution frameworks.
    Zoroastrianism is foundational to Iranian cultural identity.
    """
    log.info("Collecting all religious traditions...")
    count = 0

    # Bible — peace, justice, war passages
    bible_chapters = [
        (5, "Matthew", "Sermon on Mount — Peacemakers blessed"),
        (6, "Romans", "Peace with enemies — love your enemy"),
        (20, "Deuteronomy", "Laws of war — ancient rules of engagement"),
        (21, "Isaiah", "Swords into plowshares — peace prophecy"),
        (82, "Psalms", "Justice for oppressed — divine justice"),
    ]
    for num, name, theme in bible_chapters:
        try:
            r = requests.get(f"https://bible-api.com/{name}+{num}?translation=web", timeout=10)
            if r.status_code != 200: continue
            data = r.json()
            verses = data.get("verses", [])
            text = f"Bible {name} {num} ({theme}): " + " ".join(v.get("text","") for v in verses[:15])
            _save(_rec("Bible (World English Bible)", f"https://bible-api.com/{name}+{num}",
                "Global", "Christian-scripture", "~100 CE", "en", "religious_texts",
                ["iran_hormuz", "afghanistan"], text[:3000],
                notes=f"Bible chapter on {theme} — conflict/justice/peace"), "all_religions")
            count += 1
        except Exception as e: log.error(f"Bible {name} {num}: {e}")

    # Torah/Hebrew Bible passages
    torah_searches = [
        "Torah justice peace war shalom Hebrew Bible",
        "Talmud conflict resolution Jewish law ethics",
        "Jewish law just war pikuach nefesh self defense",
    ]
    for q in torah_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 10, "output": "json"}, timeout=15)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Jewish/Torah: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global", "Jewish-scripture-theology", doc.get("date",""),
                    "en", "religious_texts", ["iran_hormuz", "afghanistan"], text,
                    notes=f"Torah/Jewish law: {q}"), "all_religions")
                count += 1
        except Exception as e: log.error(f"Torah '{q}': {e}")

    # Hindu texts — Dharma, Karma, just war (Mahabharata/Bhagavad Gita)
    hindu_searches = [
        "Bhagavad Gita war dharma duty Arjuna Krishna",
        "Hindu nationalism India Pakistan Afghanistan geopolitics",
        "Mahabharata war ethics dharma yudha just war",
    ]
    for q in hindu_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 10, "output": "json"}, timeout=15)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Hindu: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global", "Hindu-scripture-philosophy", doc.get("date",""),
                    "en", "religious_texts", ["iran_hormuz", "afghanistan"], text,
                    notes=f"Hindu text: {q}"), "all_religions")
                count += 1
        except Exception as e: log.error(f"Hindu '{q}': {e}")

    # Buddhist texts — non-violence, compassion, conflict resolution
    buddhist_searches = [
        "Buddhist non-violence ahimsa conflict peace resolution",
        "Dhammapada peace anger hatred wisdom conflict",
        "Buddhist ethics war compassion political philosophy",
    ]
    for q in buddhist_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 10, "output": "json"}, timeout=15)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Buddhist: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global", "Buddhist-philosophy", doc.get("date",""),
                    "en", "religious_texts", ["iran_hormuz", "afghanistan"], text,
                    notes=f"Buddhist text: {q}"), "all_religions")
                count += 1
        except Exception as e: log.error(f"Buddhist '{q}': {e}")

    # Zoroastrian texts — foundational to Iranian cultural identity
    zoroastrian_searches = [
        "Avesta Zoroastrian scripture Iran Persian identity",
        "Zoroastrianism good evil conflict Ahura Mazda Angra Mainyu",
        "Zoroastrian ethics justice Iran pre-Islamic cultural roots",
    ]
    for q in zoroastrian_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 10, "output": "json"}, timeout=15)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Zoroastrian: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Iran", "Zoroastrian-scripture", doc.get("date",""),
                    "en", "religious_texts", ["iran_hormuz"], text,
                    notes=f"Zoroastrian: {q}"), "all_religions")
                count += 1
        except Exception as e: log.error(f"Zoroastrian '{q}': {e}")

    log.info(f"All religious traditions: {count}")
    return count

def collect_demographics():
    """
    Ethnic maps, displacement data, population surveys, minority data.
    Conflict is about people. Who lives where, who was forced to move,
    who is being erased — this is the demographic truth of conflict.
    """
    log.info("Collecting demographic data...")
    count = 0
    # World Bank population/demographic indicators
    demo_indicators = [
        ("SP.POP.TOTL", "population_total"),
        ("SP.URB.TOTL.IN.ZS", "urban_population_pct"),
        ("SM.POP.REFG", "refugee_population_by_origin"),
        ("SM.POP.REFG.OR", "refugees_under_UNHCR_mandate"),
        ("VC.IHR.PSRC.P5", "intentional_homicides_per_100k"),
        ("SP.POP.DPND", "age_dependency_ratio"),
        ("SE.ADT.LITR.ZS", "literacy_rate"),
        ("SH.DYN.MORT", "child_mortality"),
    ]
    for code, name in demo_indicators:
        for iso, pilot in [("AFG", "afghanistan"), ("IRN", "iran_hormuz")]:
            try:
                r = requests.get(
                    f"https://api.worldbank.org/v2/country/{iso}/indicator/{code}",
                    params={"format": "json", "per_page": 25, "mrv": 25}, timeout=15)
                if r.status_code != 200: continue
                data = r.json()
                if len(data) < 2: continue
                for rec in (data[1] or []):
                    if rec.get("value") is None: continue
                    text = f"{name} for {iso}: {rec.get('value')} ({rec.get('date','')})"
                    _save(_rec("World Bank Demographics",
                        f"https://data.worldbank.org/indicator/{code}?locations={iso}",
                        iso, "World-Bank-demographic-data", rec.get("date",""),
                        "en", "demographics", [pilot], text,
                        notes=f"World Bank {name}"), "demographics")
                    count += 1
            except Exception as e: log.error(f"Demo {code}/{iso}: {e}")

    # UNHCR refugee data via IA
    refugee_searches = [
        {"q": "UNHCR Afghanistan refugee statistics annual report", "pilot": "afghanistan"},
        {"q": "UNHCR Iran refugee asylum seeker report", "pilot": "iran_hormuz"},
        {"q": "Afghanistan internal displacement IDP OCHA report", "pilot": "afghanistan"},
        {"q": "ethnic minority persecution Afghanistan Hazara Tajik", "pilot": "afghanistan"},
        {"q": "Iran ethnic minority Kurdish Baluchi Ahwazi Arab rights", "pilot": "iran_hormuz"},
    ]
    for s in refugee_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date",
                "rows": 15, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:500]}"
                if len(text) < 30: continue
                _save(_rec(f"Demographics: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Demographic-displacement-data", doc.get("date",""),
                    "en", "demographics", [s["pilot"]], text,
                    notes=f"Demographic: {s['q']}"), "demographics")
                count += 1
        except Exception as e: log.error(f"Demo '{s['q'][:40]}': {e}")
    log.info(f"Demographics: {count}")
    return count


def collect_academic_literature():
    """
    JSTOR, arXiv, academic conflict studies, peer-reviewed research.
    The scholarly layer that synthesizes everything else.
    """
    log.info("Collecting academic conflict literature...")
    count = 0
    searches = [
        {"q": "Afghanistan conflict resolution peace studies academic journal", "pilot": "afghanistan"},
        {"q": "Iran nuclear conflict international relations theory academic", "pilot": "iran_hormuz"},
        {"q": "conflict resolution theory practice bargaining negotiation", "pilot": "both"},
        {"q": "ethnic conflict root causes greed grievance theory", "pilot": "both"},
        {"q": "state failure governance collapse conflict academic", "pilot": "both"},
        {"q": "terrorism radicalization counter-terrorism academic research", "pilot": "both"},
        {"q": "civil war duration resolution recurrence academic study", "pilot": "both"},
        {"q": "sanctions effectiveness foreign policy coercion academic", "pilot": "iran_hormuz"},
        {"q": "peacebuilding post-conflict reconstruction evidence academic", "pilot": "both"},
        {"q": "Pashtun tribal governance Taliban political organization", "pilot": "afghanistan"},
        {"q": "Shia Islam political theory velayat-e faqih Iran governance", "pilot": "iran_hormuz"},
        {"q": "warlordism non-state armed actors conflict political economy", "pilot": "afghanistan"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date,creator",
                "rows": 30, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(f"Academic: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Academic", "Academic-conflict-studies", doc.get("date",""),
                    "en", "academic_literature", pilots, text,
                    notes=f"Academic: {s['q']}"), "academic_literature")
                count += 1
        except Exception as e: log.error(f"Academic '{s['q'][:40]}': {e}")
    log.info(f"Academic literature: {count}")
    return count


def run_structural_historical():
    total = 0
    total += collect_colonial_history()
    total += collect_international_law()
    total += collect_all_religious_traditions()
    total += collect_demographics()
    total += collect_academic_literature()
    log.info(f"Structural/historical complete: {total} records")
    return total

if __name__ == "__main__":
    run_structural_historical()
