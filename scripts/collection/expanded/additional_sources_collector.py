#!/usr/bin/env python3
"""
Additional Sources Collector — CR-AI
Fills remaining gaps: media diversity, economic inequality,
migration/diaspora data, health/humanitarian crises, environmental data,
space/satellite imagery analysis reports, judicial records.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "additional.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "additional_sources"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="medium", notes=""):
    return {
        "id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": sn, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": "additional_sources", "pilot_conflicts": pilots,
        "conflict_types": [], "text": text[:3000], "confidence": conf,
        "notes": notes, "collected_at": datetime.utcnow().isoformat()
    }

def _save(rec, sub):
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _ia(q, rows=25):
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": q, "fl[]": "identifier,title,description,date,creator",
            "rows": rows, "output": "json"}, timeout=20)
        if r.status_code == 200:
            return r.json().get("response", {}).get("docs", [])
    except Exception as e: log.error(f"IA '{q[:40]}': {e}")
    return []

def _save_ia_docs(docs, prefix, country, perspective, pilots, sub, q):
    count = 0
    for doc in docs:
        desc = doc.get("description", "")
        if isinstance(desc, list): desc = " ".join(desc)
        creator = doc.get("creator", "")
        if isinstance(creator, list): creator = "; ".join(creator)
        text = f"{doc.get('title','')}. {creator}. {desc[:500]}"
        if len(text) < 30: continue
        _save(_rec(f"{prefix}: {doc.get('title','')[:50]}",
            f"https://archive.org/details/{doc.get('identifier','')}",
            country, perspective, doc.get("date",""), "en", pilots, text,
            notes=f"Search: {q}"), sub)
        count += 1
    return count


def collect_media_diversity():
    """
    Media from every region — not just Western outlets.
    Al Jazeera, RT, CGTN, Press TV, TRT World, Dawn, The Hindu,
    Middle East Eye, +972 Magazine, Afghan news in Dari/Pashto.
    """
    log.info("Collecting diverse media sources...")
    count = 0
    sources = [
        # Global South + regional media
        ("Al Jazeera investigative report Afghanistan Iran conflict", "Qatar", "Al-Jazeera-perspective", ["iran_hormuz","afghanistan"]),
        ("Middle East Eye Iran Afghanistan analysis report", "UK-ME", "Middle-East-Eye", ["iran_hormuz","afghanistan"]),
        ("RT Russia Today analysis Afghanistan Iran geopolitics", "Russia", "RT-Russian-state", ["iran_hormuz","afghanistan"]),
        ("CGTN China Global Television Network Afghanistan Iran analysis", "China", "CGTN-Chinese-state", ["iran_hormuz","afghanistan"]),
        ("Dawn Pakistan newspaper Afghanistan Taliban analysis", "Pakistan", "Dawn-Pakistan", ["afghanistan"]),
        ("TRT World Turkey analysis Middle East Iran conflict", "Turkey", "TRT-Turkish", ["iran_hormuz","afghanistan"]),
        ("The Hindu India analysis Afghanistan Pakistan stability", "India", "Hindu-Indian-perspective", ["afghanistan"]),
        ("+972 Magazine Israel Palestine Iran conflict analysis", "Israel", "972-Israeli-independent", ["iran_hormuz"]),
        ("Ariana News Afghan news Dari Pashto Taliban", "Afghanistan", "Afghan-Ariana-News", ["afghanistan"]),
        ("Etilaatroz Afghan newspaper independent Taliban press", "Afghanistan", "Afghan-Etilaatroz", ["afghanistan"]),
        ("IranWire independent Iran journalism diaspora", "Iran", "IranWire-independent", ["iran_hormuz"]),
        ("Zan Times Afghan women journalists underground news", "Afghanistan", "Zan-Times-Afghan-women", ["afghanistan"]),
    ]
    for q, country, perspective, pilots in sources:
        docs = _ia(q, rows=15)
        count += _save_ia_docs(docs, "Media", country, perspective, pilots, "media_diversity", q)
    log.info(f"Media diversity: {count}")
    return count


def collect_inequality_poverty_data():
    """
    Economic inequality, poverty, Gini coefficients.
    Inequality is a structural driver of conflict — consistently underrepresented.
    The gap between elites and populations is one of the most reliable
    predictors of political violence.
    """
    log.info("Collecting inequality and poverty data...")
    count = 0

    # World Bank inequality indicators
    wb_indicators = [
        ("SI.POV.GINI", "gini_coefficient"),
        ("SI.POV.DDAY", "poverty_headcount_1.90_per_day"),
        ("NY.GNP.PCAP.CD", "GNI_per_capita"),
        ("SI.DST.10TH.10", "income_share_top_10_pct"),
        ("SI.DST.FRST.20", "income_share_bottom_20_pct"),
        ("SH.STA.STNT.ZS", "stunting_children_pct"),
        ("SH.H2O.BASW.ZS", "basic_water_access_pct"),
    ]
    for code, name in wb_indicators:
        for iso, pilot in [("AFG","afghanistan"),("IRN","iran_hormuz")]:
            try:
                r = requests.get(f"https://api.worldbank.org/v2/country/{iso}/indicator/{code}",
                    params={"format":"json","per_page":20,"mrv":20}, timeout=15)
                if r.status_code != 200: continue
                data = r.json()
                if len(data) < 2: continue
                for rec in (data[1] or []):
                    if rec.get("value") is None: continue
                    text = f"Inequality indicator {name} for {iso}: {rec.get('value')} ({rec.get('date','')})"
                    _save(_rec("World Bank Inequality Data",
                        f"https://data.worldbank.org/indicator/{code}?locations={iso}",
                        iso, "World-Bank-inequality", rec.get("date",""), "en", [pilot], text,
                        conf="high", notes=f"WB inequality: {name}"), "inequality_poverty")
                    count += 1
            except Exception as e: log.error(f"WB inequality {code}/{iso}: {e}")

    # IA searches for inequality and conflict studies
    for q, pilot in [
        ("economic inequality conflict onset grievance study", "both"),
        ("Afghanistan inequality warlord elite capture reconstruction", "afghanistan"),
        ("Iran income inequality sanctions rich poor disparity", "iran_hormuz"),
        ("resource curse oil wealth inequality political instability", "iran_hormuz"),
    ]:
        pilots = ["iran_hormuz","afghanistan"] if pilot == "both" else [pilot]
        count += _save_ia_docs(_ia(q), "Inequality", "Multiple",
            "Inequality-conflict-research", pilots, "inequality_poverty", q)

    log.info(f"Inequality/poverty: {count}")
    return count


def collect_diaspora_migration():
    """
    Diaspora networks, migration patterns, refugee integration.
    The Afghan diaspora is 6+ million people. The Iranian diaspora
    is 5+ million. These are political actors, financial conduits,
    and cultural bridges — almost entirely absent from conflict analysis.
    """
    log.info("Collecting diaspora and migration data...")
    count = 0
    searches = [
        ("Afghan diaspora political activism remittances conflict", "afghanistan"),
        ("Afghan refugee Europe Germany integration politics", "afghanistan"),
        ("Iranian diaspora political opposition activism abroad", "iran_hormuz"),
        ("Iranian American dual citizen geopolitics sanctions", "iran_hormuz"),
        ("remittances conflict country economic lifeline diaspora", "both"),
        ("refugee return post-conflict conditions willingness survey", "both"),
        ("brain drain conflict professional emigration impact", "both"),
        ("diaspora funding conflict financing homeland politics", "both"),
        ("transnational community identity belonging homeland conflict", "both"),
        ("undocumented migration conflict push factor desperation", "both"),
    ]
    for q, pilot in searches:
        pilots = ["iran_hormuz","afghanistan"] if pilot == "both" else [pilot]
        count += _save_ia_docs(_ia(q), "Diaspora/Migration", "Multiple",
            "Diaspora-migration-data", pilots, "diaspora_migration", q)
    log.info(f"Diaspora/migration: {count}")
    return count


def collect_health_crisis_data():
    """
    Health crises as conflict indicators and drivers.
    Cholera outbreaks signal governance collapse. Maternal mortality
    signals oppression. Mental health crisis signals societal trauma.
    Afghanistan has among the world's worst health indicators.
    """
    log.info("Collecting health crisis data...")
    count = 0

    # WHO health indicators via World Bank
    health_indicators = [
        ("SH.DYN.MORT",     "child_mortality_per_1000"),
        ("SH.STA.MMRT",     "maternal_mortality_per_100k"),
        ("SH.MED.PHYS.ZS",  "physicians_per_1000"),
        ("SH.XPD.CHEX.PC.CD","health_expenditure_per_capita"),
        ("SP.DYN.LE00.IN",  "life_expectancy"),
        ("SH.TBS.INCD",     "tuberculosis_incidence"),
        ("SN.ITK.DEFC.ZS",  "undernourishment_pct"),
    ]
    for code, name in health_indicators:
        for iso, pilot in [("AFG","afghanistan"),("IRN","iran_hormuz")]:
            try:
                r = requests.get(f"https://api.worldbank.org/v2/country/{iso}/indicator/{code}",
                    params={"format":"json","per_page":20,"mrv":20}, timeout=15)
                if r.status_code != 200: continue
                data = r.json()
                if len(data) < 2: continue
                for rec in (data[1] or []):
                    if rec.get("value") is None: continue
                    text = f"Health indicator {name} for {iso}: {rec.get('value')} ({rec.get('date','')})"
                    _save(_rec("World Bank Health Data",
                        f"https://data.worldbank.org/indicator/{code}?locations={iso}",
                        iso, "WHO-World-Bank-health", rec.get("date",""), "en", [pilot], text,
                        conf="high", notes=f"WB health: {name}"), "health_crisis")
                    count += 1
            except Exception as e: log.error(f"WB health {code}/{iso}: {e}")

    # IA health conflict searches
    for q, pilot in [
        ("Afghanistan health crisis malnutrition famine collapse", "afghanistan"),
        ("Iran mental health sanctions impact psychological wellbeing", "iran_hormuz"),
        ("conflict health system collapse hospital attack war crimes", "both"),
        ("cholera outbreak conflict water sanitation displacement", "both"),
    ]:
        pilots = ["iran_hormuz","afghanistan"] if pilot == "both" else [pilot]
        count += _save_ia_docs(_ia(q), "Health", "Multiple",
            "Health-crisis-conflict", pilots, "health_crisis", q)

    log.info(f"Health crisis: {count}")
    return count


def collect_social_media_expanded():
    """
    Expand social media beyond Reddit — Twitter/X archives, TikTok reports,
    YouTube channel analysis, Clubhouse/podcast discussions.
    The new public square where conflicts are fought narratively.
    """
    log.info("Collecting expanded social media analysis...")
    count = 0
    searches = [
        ("Twitter social media Iran protest hashtag analysis 2022", "iran_hormuz"),
        ("TikTok Afghanistan Taliban social media propaganda analysis", "afghanistan"),
        ("YouTube Persian Farsi political commentary channel Iran", "iran_hormuz"),
        ("social media disinformation bot network Iran Afghanistan analysis", "both"),
        ("Telegram channel political opposition Iran Afghanistan monitor", "both"),
        ("Instagram influencer political protest Iran suppression", "iran_hormuz"),
        ("WhatsApp misinformation conflict spreading Middle East", "both"),
        ("podcast discussion Afghanistan Iran geopolitics commentary", "both"),
    ]
    for q, pilot in searches:
        pilots = ["iran_hormuz","afghanistan"] if pilot == "both" else [pilot]
        count += _save_ia_docs(_ia(q), "Social Media+", "Multiple",
            "Expanded-social-media-analysis", pilots, "social_media_expanded", q)
    log.info(f"Expanded social media: {count}")
    return count


def run_additional_sources():
    total = 0
    total += collect_media_diversity()
    total += collect_inequality_poverty_data()
    total += collect_diaspora_migration()
    total += collect_health_crisis_data()
    total += collect_social_media_expanded()
    log.info(f"Additional sources complete: {total} records")
    return total

if __name__ == "__main__":
    run_additional_sources()
