#!/usr/bin/env python3
"""
Historical Depth Collector — CR-AI
Goes back as far as records exist. Ancient conflicts, medieval wars,
early modern empires. The deep roots of today's conflicts.

Sources:
  - Project Gutenberg: Full texts of Thucydides, Herodotus, Sun Tzu, Ibn Khaldun,
    Machiavelli, Kautilya's Arthashastra, classical war histories
  - Internet Archive: Historical newspapers, colonial records, war diaries
  - Wikisource: Primary source documents in public domain
  - Open Library: Full text books on conflict history
  - Perseus Digital Library: Greek/Latin classical texts on war and politics
  - Standard Ebooks: Cleaned public domain political philosophy
  
Time periods covered:
  3000 BCE — Ancient Mesopotamia, Egypt, Persia
  500 BCE  — Classical Greece, Persian Wars, Alexander
  0 CE     — Rome, Parthia, Sassanid-Byzantine wars
  700 CE   — Islamic expansion, Crusades, Mongol conquest
  1400 CE  — Ottoman expansion, Safavid Iran, Mughal India
  1700 CE  — European colonialism, Great Game, Afghan empires
  1800 CE  — Anglo-Afghan wars, imperial partition, nationalism
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "historical_depth.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT = BASE_DIR / "data" / "raw" / "historical_depth"
OUT.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="medium", notes=""):
    return {"id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
            "source_name": sn, "source_url": url, "source_country": country,
            "source_perspective": perspective, "date": date, "language": lang,
            "category": "historical_depth", "pilot_conflicts": pilots,
            "conflict_types": [], "text": text[:3000], "confidence": conf,
            "notes": notes, "collected_at": datetime.utcnow().isoformat()}

def _save(rec, sub):
    p = OUT / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl","a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")

def _ia(q, rows=25):
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": q, "fl[]": "identifier,title,description,date,creator",
            "rows": rows, "output": "json"}, timeout=20)
        if r.status_code==200:
            return r.json().get("response",{}).get("docs",[])
    except Exception as e: log.error(f"IA '{q[:40]}': {e}")
    return []

def _save_ia(docs, prefix, country, perspective, pilots, sub, q):
    count = 0
    for doc in docs:
        desc = doc.get("description","")
        if isinstance(desc,list): desc=" ".join(desc)
        creator = doc.get("creator","")
        if isinstance(creator,list): creator="; ".join(creator)
        text = f"{doc.get('title','')}. {creator}. {desc[:500]}"
        if len(text)<30: continue
        _save(_rec(f"{prefix}: {doc.get('title','')[:50]}",
            f"https://archive.org/details/{doc.get('identifier','')}",
            country, perspective, doc.get("date",""), "en", pilots, text,
            notes=f"Historical: {q}"), sub)
        count += 1
    return count


def collect_classical_texts():
    """Ancient and classical texts on war, governance, conflict resolution."""
    log.info("Collecting classical texts...")
    count = 0
    # Project Gutenberg API for key works
    gutenberg_works = [
        (2015, "Thucydides - History of Peloponnesian War", "Greece", "Greek-classical"),
        (2456, "Herodotus - Histories (Persian Wars)", "Greece", "Greek-classical"),
        (1262, "Sun Tzu - Art of War", "China", "Chinese-classical-strategy"),
        (2088, "Kautilya - Arthashastra (Indian statecraft)", "India", "Indian-classical"),
        (1400, "Machiavelli - The Prince", "Italy", "European-political-philosophy"),
        (13268,"Ibn Khaldun - Muqaddimah (Islamic social theory)", "Tunisia", "Islamic-social-theory"),
        (44937,"Caesar - Gallic Wars", "Rome", "Roman-classical"),
        (14627,"Plutarch - Lives (Greek/Roman leaders)", "Greece", "Greco-Roman"),
        (23700,"Polybius - Histories (Roman expansion)", "Rome", "Roman-classical"),
    ]
    for gid, title, country, perspective in gutenberg_works:
        try:
            r = requests.get(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
                timeout=20)
            if r.status_code != 200: continue
            # Take first 2000 chars — enough for context
            text = f"Classical text: {title}. " + r.text[:2000].replace("\r\n"," ")
            _save(_rec(title, f"https://www.gutenberg.org/ebooks/{gid}",
                country, perspective, "ancient", "en",
                ["iran_hormuz","afghanistan"], text, conf="high",
                notes=f"Gutenberg #{gid}: {title}"), "classical_texts")
            count += 1
        except Exception as e: log.error(f"Gutenberg {gid}: {e}")

    # IA searches for classical works
    ia_searches = [
        ("Thucydides Peloponnesian War conflict analysis history", "Greece", "Greek-classical"),
        ("Herodotus Persian Wars Achaemenid empire conflict", "Persia", "Persian-classical"),
        ("Ibn Khaldun asabiyya tribal solidarity conflict theory", "Arab", "Islamic-social-theory"),
        ("Kautilya Arthashastra statecraft war diplomacy India", "India", "Indian-classical"),
        ("Sun Tzu Art of War strategy conflict resolution ancient", "China", "Chinese-strategy"),
        ("Xenophon Anabasis Persian expedition ancient war", "Greece", "Greek-Persian"),
    ]
    for q, country, perspective in ia_searches:
        count += _save_ia(_ia(q,15), "Classical", country, perspective,
            ["iran_hormuz","afghanistan"], "classical_texts", q)
    log.info(f"Classical texts: {count}")
    return count


def collect_islamic_golden_age():
    """
    Islamic Golden Age scholarship — al-Farabi, al-Mawardi, Ibn Rushd, al-Ghazali.
    Islamic political theory, governance philosophy, just war doctrine.
    This is the intellectual foundation that DIRECTLY shapes Taliban ideology,
    Iranian political theology, and Islamic ADR frameworks.
    """
    log.info("Collecting Islamic Golden Age scholarship...")
    count = 0
    searches = [
        ("al-Mawardi Islamic governance caliphate political theory Arabic", "Iraq", "Islamic-political-theory"),
        ("al-Farabi ideal state philosophy governance Islamic", "Iraq", "Islamic-philosophy"),
        ("Ibn Rushd Averroes political philosophy Islamic just war", "Spain", "Islamic-philosophy"),
        ("al-Ghazali governance ethics Islamic political thought", "Iran", "Islamic-ethics"),
        ("Ibn Taymiyya jihad governance Islamic political theology", "Syria", "Islamic-political-theology"),
        ("Islamic jurisprudence fiqh war peace treaty law", "Multiple", "Islamic-law"),
        ("Sharia law conflict resolution mediation sulh", "Multiple", "Islamic-ADR"),
        ("Sufi tradition peace reconciliation conflict resolution", "Multiple", "Sufi-peace"),
        ("Islamic Golden Age political philosophy translation movement", "Multiple", "Islamic-scholarship"),
        ("Mutazilite rationalism Islamic theology state power", "Iraq", "Islamic-rationalism"),
    ]
    for q, country, perspective in searches:
        count += _save_ia(_ia(q,15), "Islamic Golden Age", country, perspective,
            ["iran_hormuz","afghanistan"], "islamic_golden_age", q)
    log.info(f"Islamic Golden Age: {count}")
    return count


def collect_ottoman_safavid_mughal():
    """
    Ottoman, Safavid, and Mughal empires — the immediate ancestors
    of today's Middle East and Central Asian state system.
    The Safavid-Ottoman war shaped Shia-Sunni geopolitics forever.
    The Mughal collapse created the vacuum the British filled.
    """
    log.info("Collecting Ottoman/Safavid/Mughal records...")
    count = 0
    searches = [
        ("Ottoman Empire expansion governance millet system minorities", "Turkey", "Ottoman-governance"),
        ("Ottoman Safavid war Shia Sunni conflict 16th century", "Turkey", "Ottoman-Safavid-conflict"),
        ("Safavid Iran Shia state formation Persian identity", "Iran", "Safavid-Iranian"),
        ("Safavid dynasty governance Isfahan military conflict", "Iran", "Safavid-Persian"),
        ("Mughal India decline British East India Company conflict", "India", "Mughal-Indian"),
        ("Ottoman collapse Middle East partition mandate borders", "Multiple", "Post-Ottoman"),
        ("Tanzimat Ottoman reform nationalism ethnic conflict", "Turkey", "Ottoman-reform"),
        ("Ottoman Armenia Balkans ethnic conflict genocide history", "Multiple", "Ottoman-ethnic"),
        ("Safavid Afghan war Hotaki dynasty collapse 1722", "Afghanistan", "Safavid-Afghan"),
        ("Durrani Afghan empire formation Pashtun history 18th century", "Afghanistan", "Afghan-Durrani"),
    ]
    for q, country, perspective in searches:
        count += _save_ia(_ia(q,15), "Ottoman/Safavid/Mughal", country, perspective,
            ["iran_hormuz","afghanistan"], "ottoman_safavid_mughal", q)
    log.info(f"Ottoman/Safavid/Mughal: {count}")
    return count


def collect_colonial_primary_sources():
    """
    Primary colonial documents — the actual papers that created today's borders.
    Sykes-Picot text. Durand Line agreement. Balfour Declaration.
    Anglo-Afghan treaties. Not summaries — the actual documents.
    """
    log.info("Collecting colonial primary source documents...")
    count = 0
    searches = [
        ("Sykes Picot agreement 1916 text French British Middle East", "UK/France", "Sykes-Picot-primary"),
        ("Durand Line agreement 1893 text British Abdur Rahman", "UK/Afghanistan", "Durand-Line-primary"),
        ("Balfour Declaration 1917 text British Palestine Jewish", "UK", "Balfour-primary"),
        ("Anglo-Afghan treaty 1919 1921 text independence", "UK/Afghanistan", "Anglo-Afghan-treaty"),
        ("Anglo-Persian agreement 1919 British Iran oil", "UK/Iran", "Anglo-Persian-primary"),
        ("League of Nations mandate Palestine Iraq Syria text", "International", "League-Mandate"),
        ("British India partition 1947 Radcliffe line border document", "UK/India", "Partition-primary"),
        ("Qajar dynasty treaty Iran capitulation colonial", "Iran", "Qajar-colonial"),
        ("Great Game British Russian Central Asia diplomacy documents", "UK/Russia", "Great-Game-primary"),
        ("Berlin Congress 1878 Ottoman territory partition text", "Europe", "Berlin-Congress"),
        ("Treaty Westphalia 1648 sovereignty state system text", "Europe", "Westphalia-primary"),
        ("East India Company charter records Afghan trade colonial", "UK", "EIC-Afghanistan"),
    ]
    for q, country, perspective in searches:
        count += _save_ia(_ia(q,15), "Colonial Primary", country, perspective,
            ["iran_hormuz","afghanistan"], "colonial_primary_sources", q)
    log.info(f"Colonial primary sources: {count}")
    return count


def collect_world_wars_cold_war():
    """
    WWI, WWII, and Cold War — direct causal chains to today's conflicts.
    Anglo-Soviet occupation of Iran 1941. US-Soviet proxy wars in Afghanistan.
    CIA Operation TPAJAX (1953 Iran coup). Operation Cyclone (mujahedeen).
    """
    log.info("Collecting World Wars and Cold War records...")
    count = 0
    searches = [
        ("Anglo-Soviet invasion Iran 1941 WWII occupation", "UK/USSR/Iran", "WWII-Iran"),
        ("CIA Operation TPAJAX 1953 Iran Mossadegh coup documents", "USA/Iran", "CIA-Iran-1953"),
        ("Operation Cyclone CIA mujahedeen Afghanistan Cold War", "USA", "CIA-Afghanistan"),
        ("Soviet Afghan war 1979 Politburo decision invasion", "USSR", "Soviet-Afghan"),
        ("US Iran hostage crisis 1979 diplomatic breakdown", "USA/Iran", "Iran-Hostage"),
        ("Cold War proxy war Third World conflict superpower", "USA/USSR", "Cold-War-proxy"),
        ("Reagan Doctrine contra covert operation anti-communist", "USA", "Reagan-Doctrine"),
        ("détente Helsinki Accords human rights Cold War", "International", "Cold-War-détente"),
        ("Non-Aligned Movement Bandung Cold War neutrality", "Multiple", "Non-Aligned"),
        ("Truman Doctrine containment Iran Turkey 1947", "USA", "Truman-Doctrine-Iran"),
        ("CENTO Baghdad Pact Iran Middle East Cold War", "Multiple", "CENTO-pact"),
        ("KGB SAVAK intelligence cooperation Iran Cold War", "USSR/Iran", "KGB-SAVAK"),
    ]
    for q, country, perspective in searches:
        count += _save_ia(_ia(q,15), "WWs/Cold War", country, perspective,
            ["iran_hormuz","afghanistan"], "world_wars_cold_war", q)
    log.info(f"WWs/Cold War: {count}")
    return count


def run_historical_depth():
    total = 0
    total += collect_classical_texts()
    total += collect_islamic_golden_age()
    total += collect_ottoman_safavid_mughal()
    total += collect_colonial_primary_sources()
    total += collect_world_wars_cold_war()
    log.info(f"Historical depth complete: {total}")
    return total

if __name__ == "__main__":
    run_historical_depth()
