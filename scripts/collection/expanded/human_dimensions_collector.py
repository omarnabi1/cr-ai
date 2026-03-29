#!/usr/bin/env python3
"""
Human Dimensions Collector — CR-AI Expanded Dataset
Captures the soul of conflict: survivor testimony, psychology, propaganda,
conspiracy theories, protest art, cultural expression.

These are NOT noise. They ARE the belief systems that mobilize populations.
You cannot understand why people fight without understanding what they believe,
even when — especially when — it is false or contested.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "human_dimensions.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "human_dimensions"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(source_name, url, country, perspective, date, lang, category,
         pilots, text, confidence="medium", notes="", extra=None):
    r = {
        "id": hashlib.sha256(f"{source_name}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": source_name, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": category, "pilot_conflicts": pilots, "conflict_types": [],
        "text": text[:3000], "confidence": confidence, "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }
    if extra: r.update(extra)
    return r

def _save(rec, sub): 
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def collect_oral_histories():
    """
    Oral histories and survivor testimonies from Internet Archive, USC Shoah,
    and open oral history projects. The lived experience layer.
    """
    log.info("Collecting oral histories and survivor testimonies...")
    count = 0
    searches = [
        {"q": "oral history Afghanistan war survivor testimony", "pilot": "afghanistan"},
        {"q": "Afghan refugee testimony displacement story", "pilot": "afghanistan"},
        {"q": "Hazara persecution testimony witness account", "pilot": "afghanistan"},
        {"q": "Taliban rule Afghan woman testimony firsthand", "pilot": "afghanistan"},
        {"q": "Iran revolution oral history 1979 survivor", "pilot": "iran_hormuz"},
        {"q": "Iran sanctions impact civilian testimony personal account", "pilot": "iran_hormuz"},
        {"q": "Iran protest 2022 Mahsa Amini witness account", "pilot": "iran_hormuz"},
        {"q": "war trauma PTSD civilian conflict survivor narrative", "pilot": "both"},
        {"q": "refugee camp oral history Middle East displacement", "pilot": "both"},
        {"q": "child soldier testimony armed conflict recruitment", "pilot": "both"},
    ]
    for s in searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": s["q"], "fl[]": "identifier,title,description,date,creator",
                "rows": 30, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", ""); 
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                rec = _rec(f"IA Oral History: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Lived-experience-testimony", doc.get("date",""),
                    "en", "oral_history", pilots, text,
                    notes=f"Oral history search: {s['q']}")
                _save(rec, "oral_histories"); count += 1
        except Exception as e: log.error(f"Oral history '{s['q'][:40]}': {e}")
    log.info(f"Oral histories: {count}")
    return count


def collect_psychology_trauma():
    """
    Psychological studies on conflict, trauma, group identity, and radicalization.
    Understanding the mind is understanding the war.
    """
    log.info("Collecting psychology and trauma research...")
    count = 0
    searches = [
        {"q": "conflict psychology collective trauma war PTSD population", "pilot": "both"},
        {"q": "group identity ethnic nationalism radicalization psychology", "pilot": "both"},
        {"q": "dehumanization enemy propaganda psychological warfare study", "pilot": "both"},
        {"q": "Afghanistan civilian trauma mental health displacement", "pilot": "afghanistan"},
        {"q": "Iran population psychology authoritarian regime resistance", "pilot": "iran_hormuz"},
        {"q": "grief mourning loss war bereaved family conflict", "pilot": "both"},
        {"q": "child trauma war conflict development impact study", "pilot": "both"},
        {"q": "combatant psychology soldier motivation ideology", "pilot": "both"},
        {"q": "reconciliation forgiveness post-conflict psychology peacebuilding", "pilot": "both"},
        {"q": "in-group out-group tribal psychology conflict escalation", "pilot": "both"},
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
                rec = _rec(f"Psychology: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Academic", "Conflict-psychology-research", doc.get("date",""),
                    "en", "psychology_trauma", pilots, text,
                    notes=f"Psychology search: {s['q']}")
                _save(rec, "psychology_trauma"); count += 1
        except Exception as e: log.error(f"Psychology '{s['q'][:40]}': {e}")
    log.info(f"Psychology/trauma: {count}")
    return count

def collect_propaganda_narratives():
    """
    State propaganda, counter-narratives, information warfare.
    These are not noise — they ARE the belief systems that mobilize populations.
    Includes all sides: US, Iranian, Taliban, Russian, Chinese framing.
    """
    log.info("Collecting propaganda and state narratives...")
    count = 0
    searches = [
        # Iranian state narrative
        {"q": "Iran state propaganda narrative foreign policy media", "pilot": "iran_hormuz", "perspective": "Iranian-state-narrative"},
        {"q": "IRGC Revolutionary Guard propaganda ideology messaging", "pilot": "iran_hormuz", "perspective": "IRGC-ideology"},
        {"q": "Iran anti-American narrative Great Satan rhetoric", "pilot": "iran_hormuz", "perspective": "Iranian-anti-western"},
        # US/Western narrative
        {"q": "US government Iran narrative axis of evil rogue state", "pilot": "iran_hormuz", "perspective": "US-state-narrative"},
        {"q": "Western media Iran framing bias analysis", "pilot": "iran_hormuz", "perspective": "Western-media-framing"},
        # Taliban narrative
        {"q": "Taliban ideology propaganda religious justification jihad", "pilot": "afghanistan", "perspective": "Taliban-ideology"},
        {"q": "Taliban media messaging Emarah Voice of Jihad", "pilot": "afghanistan", "perspective": "Taliban-media"},
        # Counter-narratives
        {"q": "Afghanistan counter-narrative civil society resistance voice", "pilot": "afghanistan", "perspective": "Afghan-counter-narrative"},
        {"q": "Iran Green Movement protest narrative 2009 2022", "pilot": "iran_hormuz", "perspective": "Iranian-opposition"},
        # Information warfare analysis
        {"q": "information warfare disinformation conflict Middle East analysis", "pilot": "both", "perspective": "Info-warfare-analysis"},
        {"q": "social media manipulation conflict narrative bot network", "pilot": "both", "perspective": "Social-media-manipulation"},
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
                rec = _rec(f"Propaganda/Narrative: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", s["perspective"], doc.get("date",""),
                    "en", "propaganda_narratives", pilots, text,
                    notes=f"Propaganda search: {s['q']}")
                _save(rec, "propaganda_narratives"); count += 1
        except Exception as e: log.error(f"Propaganda '{s['q'][:40]}': {e}")
    log.info(f"Propaganda/narratives: {count}")
    return count


def collect_conspiracy_counter_narratives():
    """
    Conspiracy theories and fringe beliefs are NOT to be dismissed.
    They represent real belief systems that drove real decisions.
    The 'Protocols' shaped Nazi policy. 9/11 conspiracies shaped invasion support.
    Deep State theories shaped Afghan withdrawal politics.
    We collect them as DATA not as truth — to understand the full information environment.
    """
    log.info("Collecting conspiracy theories and counter-narratives...")
    count = 0
    searches = [
        {"q": "Iran nuclear program conspiracy theory secret weapons", "pilot": "iran_hormuz"},
        {"q": "CIA regime change Iran conspiracy covert operation", "pilot": "iran_hormuz"},
        {"q": "Afghanistan war oil pipeline conspiracy geopolitics", "pilot": "afghanistan"},
        {"q": "Taliban CIA creation conspiracy theory mujahedeen", "pilot": "afghanistan"},
        {"q": "9/11 conspiracy theory blowback Afghanistan context", "pilot": "afghanistan"},
        {"q": "false flag operation Middle East war pretext conspiracy", "pilot": "both"},
        {"q": "deep state foreign policy conspiracy theory analysis", "pilot": "both"},
        {"q": "Zionist conspiracy Iran antisemitism propaganda", "pilot": "iran_hormuz"},
        {"q": "Afghanistan war profit military industrial complex conspiracy", "pilot": "afghanistan"},
        {"q": "color revolution regime change NGO conspiracy narrative", "pilot": "both"},
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
                rec = _rec(f"Conspiracy/Counter-narrative: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Conspiracy-counter-narrative", doc.get("date",""),
                    "en", "conspiracy_counter_narratives", pilots, text,
                    confidence="low",
                    notes=f"CONSPIRACY/FRINGE — collect as data, not truth. Search: {s['q']}")
                _save(rec, "conspiracy_counter_narratives"); count += 1
        except Exception as e: log.error(f"Conspiracy '{s['q'][:40]}': {e}")
    log.info(f"Conspiracy/counter-narratives: {count}")
    return count

def collect_culture_art_protest():
    """
    Music, poetry, film, protest art. These carry the emotional truth
    that official documents never capture. Afghan poetry under Taliban.
    Persian music under sanctions. War photography. Protest graffiti.
    """
    log.info("Collecting cultural expressions and protest art...")
    count = 0
    searches = [
        {"q": "Afghan poetry war resistance literature Dari Pashto", "pilot": "afghanistan"},
        {"q": "Persian poetry Iran revolution resistance Farsi literature", "pilot": "iran_hormuz"},
        {"q": "Afghanistan music culture banned Taliban art suppression", "pilot": "afghanistan"},
        {"q": "Iran protest song green movement music censorship", "pilot": "iran_hormuz"},
        {"q": "war photography documentary conflict photojournalism", "pilot": "both"},
        {"q": "refugee art expression displacement creative response", "pilot": "both"},
        {"q": "graffiti street art protest Middle East conflict", "pilot": "both"},
        {"q": "Afghan film cinema documentary social commentary", "pilot": "afghanistan"},
        {"q": "Iranian cinema film censorship political expression", "pilot": "iran_hormuz"},
        {"q": "conflict memoir autobiography war firsthand account book", "pilot": "both"},
        {"q": "humor satire political cartoon Middle East Iran Afghanistan", "pilot": "both"},
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
                rec = _rec(f"Culture/Art: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Cultural-artistic-expression", doc.get("date",""),
                    "en", "culture_art_protest", pilots, text,
                    notes=f"Culture/art search: {s['q']}")
                _save(rec, "culture_art_protest"); count += 1
        except Exception as e: log.error(f"Culture '{s['q'][:40]}': {e}")
    log.info(f"Culture/art/protest: {count}")
    return count


def run_human_dimensions():
    total = 0
    total += collect_oral_histories()
    total += collect_psychology_trauma()
    total += collect_propaganda_narratives()
    total += collect_conspiracy_counter_narratives()
    total += collect_culture_art_protest()
    log.info(f"Human dimensions complete: {total} records")
    return total

if __name__ == "__main__":
    run_human_dimensions()
