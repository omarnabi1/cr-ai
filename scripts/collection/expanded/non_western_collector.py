#!/usr/bin/env python3
"""
Non-Western Sources Collector — CR-AI
The most critical missing piece. Our dataset skews Western.
This collector targets primary sources from the perspectives of the
actual parties to the conflicts — not observers of them.

Targets:
  - Persian/Farsi language sources (Iranian perspective, not Western coverage of Iran)
  - Pashtun/Dari/Pashto sources (Afghan perspective, not Western coverage of Afghanistan)
  - Arabic geopolitical analysis (Arab world perspective)
  - Chinese strategic analysis (Belt and Road, regional stability framing)
  - Russian historical accounts (Soviet-Afghan war, Iran relations)
  - South Asian perspective (Pakistan, India framing of Afghanistan)
  - Pre-colonial indigenous governance records
  - Oral tradition and tribal law (Pashtunwali, jirga records)
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "non_western.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "non_western_sources"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="medium", notes=""):
    return {
        "id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": sn, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": "non_western_sources", "pilot_conflicts": pilots,
        "conflict_types": [], "text": text[:3000],
        "confidence": conf, "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }

def _save(rec, sub):
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _ia(query, rows=25):
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": query, "fl[]": "identifier,title,description,date,creator",
            "rows": rows, "output": "json"}, timeout=20)
        if r.status_code == 200:
            return r.json().get("response", {}).get("docs", [])
    except Exception as e:
        log.error(f"IA query '{query[:40]}': {e}")
    return []

def _process_ia_docs(docs, source_name_prefix, country, perspective, pilots, lang, sub, search_q):
    count = 0
    for doc in docs:
        desc = doc.get("description", "")
        if isinstance(desc, list): desc = " ".join(desc)
        creator = doc.get("creator", "")
        if isinstance(creator, list): creator = "; ".join(creator)
        text = f"{doc.get('title','')}. Creator: {creator}. {desc[:600]}"
        if len(text) < 30: continue
        _save(_rec(f"{source_name_prefix}: {doc.get('title','')[:50]}",
            f"https://archive.org/details/{doc.get('identifier','')}",
            country, perspective, doc.get("date",""), lang, pilots, text,
            notes=f"Non-Western source: {search_q}"), sub)
        count += 1
    return count

def collect_persian_farsi_sources():
    """Iranian and Persian-language perspective on Iran's own conflicts."""
    log.info("Collecting Persian/Farsi language sources...")
    count = 0
    searches = [
        ("Iran revolution 1979 Persian Farsi primary source Islamic Republic", "fa", "iran_hormuz", "Iranian-primary-Persian"),
        ("Iran sanctions economic impact Persian Farsi analysis", "fa", "iran_hormuz", "Iranian-economic-analysis"),
        ("Iran nuclear program sovereignty Persian right enrichment", "fa", "iran_hormuz", "Iranian-nuclear-sovereignty"),
        ("JCPOA Iran perspective negotiations Farsi analysis", "fa", "iran_hormuz", "Iranian-JCPOA-perspective"),
        ("Iran foreign policy Persian Gulf strategy Farsi", "fa", "iran_hormuz", "Iranian-foreign-policy"),
        ("Khomeini political philosophy velayat faqih Islamic governance", "fa", "iran_hormuz", "Iranian-political-theology"),
        ("Iranian diaspora perspective Iran politics culture identity", "en", "iran_hormuz", "Iranian-diaspora"),
        ("Iran history empire civilization pre-Islamic Persia legacy", "en", "iran_hormuz", "Iranian-civilizational"),
        ("Iran protest 2019 2022 internal dissent perspective voices", "en", "iran_hormuz", "Iranian-internal-dissent"),
        ("Nowruz Persian culture identity resistance Iran", "fa", "iran_hormuz", "Persian-cultural-identity"),
    ]
    for q, lang, pilot, perspective in searches:
        docs = _ia(q)
        count += _process_ia_docs(docs, "Persian/Iranian", "Iran", perspective, [pilot], lang, "persian_farsi", q)
    log.info(f"Persian/Farsi: {count}")
    return count


def collect_pashtun_afghan_sources():
    """
    Pashtun and Afghan perspectives — the most underrepresented voice
    in Western analysis of the Afghanistan conflict.
    Pashtunwali is a complete legal and governance system.
    The jirga is a fully functional conflict resolution mechanism.
    Neither appears in Western media coverage.
    """
    log.info("Collecting Pashtun/Afghan primary sources...")
    count = 0
    searches = [
        ("Pashtunwali tribal code honor governance Pashtun law", "en", "afghanistan", "Pashtun-customary-law"),
        ("jirga tribal council Afghanistan conflict resolution decision", "en", "afghanistan", "Pashtun-jirga-governance"),
        ("Pashtun history identity nationalism border Durand line perspective", "en", "afghanistan", "Pashtun-identity"),
        ("Afghan loya jirga traditional assembly governance legitimacy", "en", "afghanistan", "Afghan-loya-jirga"),
        ("Dari Pashto Afghan literature poetry history culture", "fa", "afghanistan", "Afghan-cultural-primary"),
        ("Afghan perspective US occupation failure governance reconstruction", "en", "afghanistan", "Afghan-occupation-perspective"),
        ("Hazara history Afghanistan persecution discrimination identity", "en", "afghanistan", "Hazara-perspective"),
        ("Tajik Uzbek Hazara Northern Alliance perspective Afghanistan", "en", "afghanistan", "Non-Pashtun-Afghan"),
        ("Afghan civil society women education resistance Taliban", "en", "afghanistan", "Afghan-civil-society"),
        ("Afghanistan history empire Durrani Barakzai dynasty pre-colonial", "en", "afghanistan", "Afghan-historical-empire"),
        ("mujahedeen Afghan jihad Soviet war firsthand account Afghan voice", "en", "afghanistan", "Afghan-Soviet-war-perspective"),
        ("opium poppy farmer livelihood Afghanistan economy alternative", "en", "afghanistan", "Afghan-rural-economy"),
    ]
    for q, lang, pilot, perspective in searches:
        docs = _ia(q)
        count += _process_ia_docs(docs, "Pashtun/Afghan", "Afghanistan", perspective, [pilot], lang, "pashtun_afghan", q)
    log.info(f"Pashtun/Afghan: {count}")
    return count


def collect_arabic_regional_sources():
    """Arab world and regional perspectives on Middle East conflicts."""
    log.info("Collecting Arabic and regional perspectives...")
    count = 0
    searches = [
        ("Arab perspective Iran Saudi Arabia conflict Shia Sunni sectarian", "en", "iran_hormuz", "Arab-regional-perspective"),
        ("Palestinian Arab perspective Iran proxy Hamas resistance", "en", "iran_hormuz", "Arab-Palestine-Iran"),
        ("Arab street public opinion Iran nuclear deal sanctions", "en", "iran_hormuz", "Arab-public-opinion-Iran"),
        ("Gulf states Bahrain UAE Iran threat perception security", "en", "iran_hormuz", "Gulf-security-perspective"),
        ("Arab nationalism Nasserism pan-Arab failure legacy conflict", "en", "iran_hormuz", "Arab-nationalist-history"),
        ("Islam political thought Arab world caliphate governance theory", "en", "both", "Islamic-political-thought"),
        ("Al Jazeera Arabic perspective conflict Middle East analysis", "ar", "iran_hormuz", "Al-Jazeera-Arabic-perspective"),
        ("Ummah Muslim world solidarity geopolitics religious unity", "en", "both", "Islamic-solidarity-geopolitics"),
    ]
    pilots_map = {"both": ["iran_hormuz", "afghanistan"]}
    for q, lang, pilot, perspective in searches:
        pilots = pilots_map.get(pilot, [pilot])
        docs = _ia(q)
        count += _process_ia_docs(docs, "Arabic/Regional", "Arab World", perspective, pilots, lang, "arabic_regional", q)
    log.info(f"Arabic/regional: {count}")
    return count

def collect_chinese_russian_sources():
    """
    Chinese and Russian perspectives — two major actors whose analysis
    is almost entirely absent from Western-dominated conflict databases.
    China views Afghan stability through Belt and Road lens.
    Russia views Iran through energy and anti-NATO lens.
    Both perspectives are essential for understanding why Western solutions fail.
    """
    log.info("Collecting Chinese and Russian perspective sources...")
    count = 0

    chinese_searches = [
        ("China Belt Road Initiative Afghanistan stability interest Chinese", "en", "afghanistan", "Chinese-BRI-perspective"),
        ("China Iran relationship strategic partnership energy Chinese perspective", "en", "iran_hormuz", "Chinese-Iran-strategy"),
        ("Chinese analysis US hegemony Middle East Central Asia conflict", "en", "both", "Chinese-anti-hegemony"),
        ("Shanghai Cooperation Organisation SCO Afghanistan security Chinese", "en", "afghanistan", "Chinese-SCO-security"),
        ("China non-interference sovereignty principle conflict resolution", "en", "both", "Chinese-non-interference"),
        ("Chinese investment Afghanistan minerals copper Mes Aynak", "en", "afghanistan", "Chinese-Afghan-investment"),
    ]

    russian_searches = [
        ("Russia Soviet Afghan war history lessons analysis Russian perspective", "en", "afghanistan", "Russian-Afghan-history"),
        ("Russia Iran relationship strategic partnership military energy", "en", "iran_hormuz", "Russian-Iran-partnership"),
        ("Russian analysis NATO expansion Afghanistan regime change", "en", "afghanistan", "Russian-NATO-analysis"),
        ("Russia Central Asia security interest Afghanistan stability", "en", "afghanistan", "Russian-Central-Asia"),
        ("Soviet Afghan war veteran account memoir firsthand Russian", "en", "afghanistan", "Soviet-veteran-account"),
        ("Russia Ukraine conflict impact Iran sanctions global order", "en", "iran_hormuz", "Russian-global-order"),
    ]

    for q, lang, pilot, perspective in chinese_searches:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        docs = _ia(q)
        count += _process_ia_docs(docs, "Chinese perspective", "China", perspective, pilots, lang, "chinese_russian", q)

    for q, lang, pilot, perspective in russian_searches:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        docs = _ia(q)
        count += _process_ia_docs(docs, "Russian perspective", "Russia", perspective, pilots, lang, "chinese_russian", q)

    log.info(f"Chinese/Russian: {count}")
    return count


def collect_precolonial_indigenous():
    """
    Pre-colonial governance, indigenous legal systems, oral traditions.
    The history that existed before the Western lens arrived.
    Pashtunwali predates any Western legal framework.
    Persian governance philosophy predates modern international law.
    """
    log.info("Collecting pre-colonial and indigenous governance sources...")
    count = 0
    searches = [
        ("Pashtunwali badal melmastia nanawatai honor code tribal governance", "en", "afghanistan", "Pashtun-customary-law-precolonial"),
        ("Afghan tribal governance pre-colonial history Durrani empire", "en", "afghanistan", "Afghan-precolonial-governance"),
        ("Persian empire Achaemenid governance administration Persia ancient", "en", "iran_hormuz", "Persian-precolonial-governance"),
        ("Sassanid Persian empire governance administration legacy Iran", "en", "iran_hormuz", "Sassanid-Persian-legacy"),
        ("Islamic Golden Age governance philosophy Persian Arabic administration", "en", "both", "Islamic-golden-age"),
        ("Silk Road Central Asia trade governance pre-colonial Afghanistan Iran", "en", "both", "Silk-Road-governance"),
        ("tribal confederacy governance non-state political organization", "en", "both", "Tribal-non-state-governance"),
        ("oral law tradition dispute resolution non-Western conflict", "en", "both", "Oral-law-tradition"),
        ("pre-Islamic Iran Zoroastrian governance ethics statecraft", "en", "iran_hormuz", "Pre-Islamic-Iranian-governance"),
        ("Afghan Hazara history Mongol descendants identity precolonial", "en", "afghanistan", "Hazara-precolonial-history"),
    ]
    for q, lang, pilot, perspective in searches:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        docs = _ia(q)
        count += _process_ia_docs(docs, "Pre-colonial/Indigenous", "Multiple", perspective, pilots, lang, "precolonial_indigenous", q)
    log.info(f"Pre-colonial/indigenous: {count}")
    return count


def collect_global_south_perspectives():
    """
    Global South, postcolonial theory, decolonial analysis.
    The scholarly tradition that has been interrogating Western hegemony
    for decades — almost entirely absent from mainstream conflict databases.
    """
    log.info("Collecting Global South and postcolonial perspectives...")
    count = 0
    searches = [
        ("postcolonial theory conflict imperialism resistance Fanon Said", "en", "both", "Postcolonial-theory"),
        ("decolonial analysis Middle East Afghanistan resistance sovereignty", "en", "both", "Decolonial-analysis"),
        ("Global South perspective US foreign policy Afghanistan Iran regime", "en", "both", "Global-South-anti-imperialism"),
        ("non-aligned movement sovereignty self-determination colonial legacy", "en", "both", "Non-aligned-movement"),
        ("Edward Said orientalism Western representation Middle East", "en", "iran_hormuz", "Said-Orientalism"),
        ("Frantz Fanon colonial violence resistance national liberation", "en", "both", "Fanon-colonial-theory"),
        ("Bandung conference 1955 postcolonial solidarity Global South", "en", "both", "Bandung-postcolonial"),
        ("dependency theory economic imperialism conflict underdevelopment", "en", "both", "Dependency-theory"),
        ("Third World conflict Cold War proxy war Global South perspective", "en", "both", "Third-World-Cold-War"),
        ("subaltern studies voice oppressed conflict history non-Western", "en", "both", "Subaltern-studies"),
    ]
    for q, lang, pilot, perspective in searches:
        pilots = ["iran_hormuz", "afghanistan"] if pilot == "both" else [pilot]
        docs = _ia(q)
        count += _process_ia_docs(docs, "Global South/Postcolonial", "Multiple", perspective, pilots, lang, "global_south_postcolonial", q)
    log.info(f"Global South/postcolonial: {count}")
    return count


def run_non_western():
    total = 0
    total += collect_persian_farsi_sources()
    total += collect_pashtun_afghan_sources()
    total += collect_arabic_regional_sources()
    total += collect_chinese_russian_sources()
    total += collect_precolonial_indigenous()
    total += collect_global_south_perspectives()
    log.info(f"Non-Western sources complete: {total} records")
    return total

if __name__ == "__main__":
    run_non_western()
