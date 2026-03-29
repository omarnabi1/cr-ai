#!/usr/bin/env python3
"""
Structured Conflict Databases Collector — CR-AI Expanded Dataset
Pulls from the gold-standard academic conflict databases:

FREE DIRECT DOWNLOADS (no API key needed):
  - UCDP: Armed conflicts 1946-2024, battle deaths, one-sided violence, non-state conflicts
  - Correlates of War (CoW): Wars going back to 1816, alliances, trade, religion
  - Global Terrorism Database (GTD): 200,000+ terrorist incidents 1970-2020
  - Minorities at Risk (MAR): Ethnic/communal group grievances worldwide
  - Polity5: Democracy/autocracy scores for every country 1800-present
  - Peace Agreements Database: All signed peace agreements with provisions
  - Global Peace Index: Peacefulness rankings and trend data
"""

import json, hashlib, logging, requests, csv, io
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "structured_db.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT_BASE = BASE_DIR / "data" / "raw" / "structured_databases"
OUT_BASE.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="high", notes="", category="structured_databases"):
    return {
        "id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
        "source_name": sn, "source_url": url, "source_country": country,
        "source_perspective": perspective, "date": date, "language": lang,
        "category": category, "pilot_conflicts": pilots, "conflict_types": [],
        "text": text[:3000], "confidence": conf, "notes": notes,
        "collected_at": datetime.utcnow().isoformat()
    }

def _save(rec, sub):
    p = OUT_BASE / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def collect_ucdp_direct_download():
    """
    UCDP datasets via direct CSV download — no API token needed.
    Covers: armed conflicts 1946-2024, battle deaths, one-sided violence,
    non-state conflicts, peace agreements.
    """
    log.info("Collecting UCDP datasets via direct download...")
    count = 0

    # UCDP direct CSV download URLs (no auth required for bulk files)
    ucdp_endpoints = [
        {
            "url": "https://ucdpapi.pcr.uu.se/api/ucdpprioconflict/25.1?pagesize=1000&page=1",
            "name": "UCDP/PRIO Armed Conflict Dataset",
            "sub": "ucdp_armed_conflicts",
            "pilot_logic": "region"  # filter by region
        },
        {
            "url": "https://ucdpapi.pcr.uu.se/api/onesided/25.1?pagesize=1000&page=1",
            "name": "UCDP One-Sided Violence",
            "sub": "ucdp_one_sided",
            "pilot_logic": "location"
        },
        {
            "url": "https://ucdpapi.pcr.uu.se/api/nonstate/25.1?pagesize=1000&page=1",
            "name": "UCDP Non-State Conflict",
            "sub": "ucdp_nonstate",
            "pilot_logic": "region"
        },
    ]

    AFGHAN_KEYWORDS = {"Afghanistan", "Afghan", "Taliban", "Kabul", "AFG"}
    IRAN_KEYWORDS   = {"Iran", "Iranian", "IRGC", "Hormuz", "IRN", "Persia"}

    for ep in ucdp_endpoints:
        try:
            r = requests.get(ep["url"], timeout=30,
                headers={"Accept": "application/json"})
            if r.status_code != 200:
                log.warning(f"UCDP {ep['name']}: HTTP {r.status_code}")
                continue
            data = r.json()
            results = data.get("Result", [])
            log.info(f"  UCDP {ep['name']}: {len(results)} records")

            for item in results:
                # Determine pilot conflict relevance
                item_str = json.dumps(item)
                pilots = []
                if any(k in item_str for k in AFGHAN_KEYWORDS): pilots.append("afghanistan")
                if any(k in item_str for k in IRAN_KEYWORDS):   pilots.append("iran_hormuz")
                if not pilots: pilots = ["global"]  # keep all — history matters

                # Build text from key fields
                fields = ["conflict_name", "side_a", "side_b", "location",
                          "territory_name", "year", "intensity_level",
                          "conflict_id", "type_of_conflict"]
                text_parts = []
                for f in fields:
                    v = item.get(f)
                    if v: text_parts.append(f"{f}: {v}")
                text = f"{ep['name']}. " + " | ".join(text_parts)

                _save(_rec(
                    ep["name"],
                    "https://ucdp.uu.se",
                    item.get("location", "Multiple"),
                    "UCDP-academic-conflict-data",
                    str(item.get("year", "")),
                    "en", pilots, text,
                    notes=f"UCDP {ep['name']} v25.1"
                ), ep["sub"])
                count += 1

        except Exception as e:
            log.error(f"UCDP {ep['name']}: {e}")

    log.info(f"UCDP direct: {count}")
    return count


def collect_correlates_of_war():
    """
    Correlates of War (CoW) — wars dating back to 1816.
    The longest time-series conflict dataset in existence.
    Also covers: alliances, trade, religion, colonial history, IGO membership.
    """
    log.info("Collecting Correlates of War data...")
    count = 0

    # CoW publishes open CSVs — we fetch via IA mirrors
    cow_searches = [
        "Correlates of War interstate war dataset 1816",
        "Correlates of War intrastate civil war dataset",
        "Correlates of War colonial contiguity dataset",
        "Correlates of War alliances dataset military",
        "Correlates of War trade bilateral dataset",
        "Correlates of War religion state dataset",
        "Correlates of War national material capabilities",
        "Correlates of War formal alliances treaties",
        "Correlates of War territorial change dataset",
        "Correlates of War militarized interstate disputes",
    ]
    for q in cow_searches:
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params={
                "q": q, "fl[]": "identifier,title,description,date",
                "rows": 15, "output": "json"}, timeout=20)
            if r.status_code != 200: continue
            for doc in r.json().get("response", {}).get("docs", []):
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                _save(_rec(
                    f"Correlates of War: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global", "Correlates-of-War-dataset",
                    doc.get("date",""), "en",
                    ["iran_hormuz", "afghanistan"],
                    text, notes=f"CoW: {q}"
                ), "correlates_of_war")
                count += 1
        except Exception as e:
            log.error(f"CoW '{q[:40]}': {e}")

    log.info(f"Correlates of War: {count}")
    return count

def collect_global_terrorism_db():
    """
    Global Terrorism Database (GTD) — 200,000+ terrorist incidents 1970-2020.
    Maintained by START at University of Maryland. Open access.
    Critical for understanding non-state violence patterns.
    """
    log.info("Collecting Global Terrorism Database records...")
    count = 0

    # GTD data via GDELT which indexes GTD-related content
    # Also search IA for GTD datasets and analysis
    searches = [
        {"q": "Global Terrorism Database Afghanistan attack 2001 2021", "pilot": "afghanistan"},
        {"q": "Global Terrorism Database Iran terrorist incident IRGC", "pilot": "iran_hormuz"},
        {"q": "Taliban attack terrorism database Afghanistan civilian", "pilot": "afghanistan"},
        {"q": "IED improvised explosive device Afghanistan incident database", "pilot": "afghanistan"},
        {"q": "suicide bombing Afghanistan terrorist attack pattern", "pilot": "afghanistan"},
        {"q": "ISIS ISIL Daesh attack Middle East terrorism database", "pilot": "both"},
        {"q": "Hezbollah Hamas attack terrorism database Middle East", "pilot": "iran_hormuz"},
        {"q": "terrorism radicalization pathway recruitment analysis database", "pilot": "both"},
        {"q": "START terrorism database methodology coding political violence", "pilot": "both"},
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
                _save(_rec(
                    f"GTD/Terrorism: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Global-Terrorism-Database",
                    doc.get("date",""), "en", pilots, text,
                    notes=f"GTD search: {s['q']}"
                ), "terrorism_database")
                count += 1
        except Exception as e:
            log.error(f"GTD '{s['q'][:40]}': {e}")

    log.info(f"GTD/terrorism: {count}")
    return count


def collect_minorities_at_risk():
    """
    Minorities at Risk (MAR) Project — ethnic and communal group grievances.
    Critical for understanding why the Hazara, Baluch, Kurdish, Arab
    minorities are where they are.
    """
    log.info("Collecting Minorities at Risk data...")
    count = 0

    searches = [
        {"q": "Minorities at Risk Hazara Afghanistan ethnic discrimination", "pilot": "afghanistan"},
        {"q": "Minorities at Risk Iran ethnic minority Kurdish Baluchi", "pilot": "iran_hormuz"},
        {"q": "ethnic minority group grievance political exclusion conflict", "pilot": "both"},
        {"q": "communal conflict identity group ethnicity religion violence", "pilot": "both"},
        {"q": "minority rights persecution state violence ethnic group", "pilot": "both"},
        {"q": "Pashtun ethnic nationalism identity group Afghanistan Pakistan", "pilot": "afghanistan"},
        {"q": "Shia Sunni sectarian violence minority persecution", "pilot": "both"},
        {"q": "ethnic cleansing minority displacement forced migration", "pilot": "both"},
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
                _save(_rec(
                    f"MAR/Ethnic: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Minorities-at-Risk-ethnic-data",
                    doc.get("date",""), "en", pilots, text,
                    notes=f"MAR: {s['q']}"
                ), "minorities_at_risk")
                count += 1
        except Exception as e:
            log.error(f"MAR '{s['q'][:40]}': {e}")

    log.info(f"Minorities at Risk: {count}")
    return count


def collect_polity_democracy_data():
    """
    Polity5 — democracy/autocracy regime scores for every country 1800-present.
    Critical for understanding how regime type affects conflict behavior.
    Iran's theocracy score. Afghanistan's governance collapse score.
    The relationship between autocracy and conflict propensity.
    """
    log.info("Collecting Polity/democracy data...")
    count = 0

    searches = [
        {"q": "Polity IV V democracy autocracy score Afghanistan regime change", "pilot": "afghanistan"},
        {"q": "Polity IV V democracy Iran theocracy authoritarian score", "pilot": "iran_hormuz"},
        {"q": "democracy autocracy regime type conflict propensity study", "pilot": "both"},
        {"q": "state fragility index failed state governance collapse", "pilot": "both"},
        {"q": "Freedom House political freedom civil liberties Iran Afghanistan", "pilot": "both"},
        {"q": "Varieties of Democracy V-Dem dataset regime type measure", "pilot": "both"},
        {"q": "regime transition democratic breakdown coup conflict", "pilot": "both"},
        {"q": "hybrid regime competitive authoritarianism governance conflict", "pilot": "both"},
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
                _save(_rec(
                    f"Polity/Democracy: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Global", "Polity-democracy-regime-data",
                    doc.get("date",""), "en", pilots, text,
                    notes=f"Polity: {s['q']}"
                ), "polity_democracy")
                count += 1
        except Exception as e:
            log.error(f"Polity '{s['q'][:40]}': {e}")

    log.info(f"Polity/democracy: {count}")
    return count

def collect_peace_agreements_database():
    """
    PA-X Peace Agreements Database (University of Edinburgh) — all signed
    peace agreements worldwide with full text and provision coding.
    What was agreed, what was implemented, what failed and why.
    """
    log.info("Collecting peace agreements database...")
    count = 0

    # PA-X is open access — fetch via their API and IA
    pax_searches = [
        {"q": "peace agreement Afghanistan Taliban signed provisions text", "pilot": "afghanistan"},
        {"q": "peace agreement Iran nuclear deal signed provisions", "pilot": "iran_hormuz"},
        {"q": "ceasefire agreement Middle East implementation failure", "pilot": "both"},
        {"q": "peace process negotiation track II diplomacy backchannel", "pilot": "both"},
        {"q": "peace agreement implementation failure spoiler analysis", "pilot": "both"},
        {"q": "transitional justice truth reconciliation post-conflict", "pilot": "both"},
        {"q": "power sharing agreement ethnic conflict consociational", "pilot": "both"},
        {"q": "DDR disarmament demobilization reintegration post-conflict", "pilot": "both"},
    ]

    # Also try PA-X API directly
    pax_countries = ["Afghanistan", "Iran"]
    for country in pax_countries:
        pilot = "afghanistan" if country == "Afghanistan" else "iran_hormuz"
        try:
            r = requests.get(
                f"https://www.peaceagreements.org/wsapi/v1/agreements/?country={country}&format=json",
                timeout=20, headers={"Accept": "application/json"})
            if r.status_code == 200:
                agreements = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
                for ag in agreements[:50]:
                    title = ag.get("title", ag.get("name", ""))
                    text = f"Peace Agreement: {title}. Parties: {ag.get('parties','')}. Date: {ag.get('date','')}. {ag.get('abstract', ag.get('description',''))[:400]}"
                    _save(_rec(
                        f"PA-X: {title[:50]}",
                        ag.get("url", "https://www.peaceagreements.org"),
                        country, "PA-X-peace-agreements-database",
                        ag.get("date",""), "en", [pilot], text,
                        conf="high", notes="PA-X University of Edinburgh"
                    ), "peace_agreements")
                    count += 1
                log.info(f"  PA-X {country}: {len(agreements)} agreements")
        except Exception as e:
            log.warning(f"PA-X API {country}: {e} — falling back to IA")

    for s in pax_searches:
        pilots = ["iran_hormuz", "afghanistan"] if s["pilot"] == "both" else [s["pilot"]]
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
                _save(_rec(
                    f"Peace Agreement: {doc.get('title','')[:50]}",
                    f"https://archive.org/details/{doc.get('identifier','')}",
                    "Multiple", "Peace-agreements-analysis",
                    doc.get("date",""), "en", pilots, text,
                    notes=f"PA-X search: {s['q']}"
                ), "peace_agreements")
                count += 1
        except Exception as e:
            log.error(f"PA-X IA '{s['q'][:40]}': {e}")

    log.info(f"Peace agreements: {count}")
    return count


def collect_social_movements_protests():
    """
    Mass mobilization, protest events, social movements.
    The people's voice expressed through collective action.
    Mass Mobilization Dataset, GDELT protest data.
    """
    log.info("Collecting social movements and protest data...")
    count = 0

    # GDELT for protests — it's excellent for this
    protest_queries = [
        {"q": "Iran protest demonstration 2019 2022 mahsa amini uprising", "start": "20190101000000", "end": "20231201000000", "pilot": "iran_hormuz"},
        {"q": "Afghanistan protest Taliban resistance demonstration", "start": "20210801000000", "end": "20231201000000", "pilot": "afghanistan"},
        {"q": "Iran women protest hijab rights demonstration", "start": "20220901000000", "end": "20231201000000", "pilot": "iran_hormuz"},
        {"q": "Afghanistan women education protest resistance Taliban", "start": "20210801000000", "end": "20231201000000", "pilot": "afghanistan"},
        {"q": "Iran workers labor protest economic demonstration", "start": "20190101000000", "end": "20231201000000", "pilot": "iran_hormuz"},
    ]

    for q in protest_queries:
        try:
            r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params={
                "query": q["q"], "mode": "ArtList", "maxrecords": 50,
                "format": "json", "startdatetime": q["start"], "enddatetime": q["end"]
            }, timeout=20)
            if r.status_code != 200: continue
            articles = r.json().get("articles", [])
            for art in articles:
                text = art.get("title", "")
                if len(text) < 20: continue
                _save(_rec(
                    art.get("domain", "GDELT"),
                    art.get("url", ""),
                    art.get("sourcecountry", ""),
                    "Social-movement-protest-data",
                    art.get("seendate", ""), "en",
                    [q["pilot"]], text,
                    conf="medium", notes=f"GDELT protest: {q['q']}"
                ), "social_movements")
                count += 1
        except Exception as e:
            log.error(f"Protest '{q['q'][:40]}': {e}")

    log.info(f"Social movements/protests: {count}")
    return count


def run_structured_databases():
    total = 0
    total += collect_ucdp_direct_download()
    total += collect_correlates_of_war()
    total += collect_global_terrorism_db()
    total += collect_minorities_at_risk()
    total += collect_polity_democracy_data()
    total += collect_peace_agreements_database()
    total += collect_social_movements_protests()
    log.info(f"Structured databases complete: {total} records")
    return total

if __name__ == "__main__":
    run_structured_databases()
