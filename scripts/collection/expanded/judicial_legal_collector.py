#!/usr/bin/env python3
"""
Judicial & Legal Records Collector — CR-AI
ICC case files, ICJ rulings, war crimes tribunals, sanctions law,
international arbitration, constitutional texts, human rights law.

The law is both a weapon and a tool for resolution.
Understanding how international law has been used, abused, ignored,
and selectively enforced is essential for unbiased conflict analysis.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "judicial.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT = BASE_DIR / "data" / "raw" / "judicial_legal"
OUT.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="high", notes=""):
    return {"id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
            "source_name": sn, "source_url": url, "source_country": country,
            "source_perspective": perspective, "date": date, "language": lang,
            "category": "judicial_legal", "pilot_conflicts": pilots,
            "conflict_types": [], "text": text[:3000], "confidence": conf,
            "notes": notes, "collected_at": datetime.utcnow().isoformat()}

def _save(rec, sub):
    p = OUT / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl","a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")

def _ia(q, rows=20):
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": q, "fl[]": "identifier,title,description,date",
            "rows": rows, "output": "json"}, timeout=20)
        if r.status_code==200:
            return r.json().get("response",{}).get("docs",[])
    except Exception as e: log.error(f"IA '{q[:40]}': {e}")
    return []

def _save_ia(docs, prefix, perspective, pilots, sub, q):
    count = 0
    for doc in docs:
        desc = doc.get("description","")
        if isinstance(desc,list): desc=" ".join(desc)
        text = f"{doc.get('title','')}. {desc[:500]}"
        if len(text)<30: continue
        _save(_rec(f"{prefix}: {doc.get('title','')[:50]}",
            f"https://archive.org/details/{doc.get('identifier','')}",
            "International", perspective, doc.get("date",""), "en", pilots, text,
            notes=f"Judicial: {q}"), sub)
        count += 1
    return count


def collect_icc_icj():
    """ICC cases, ICJ rulings — international justice attempts and failures."""
    log.info("Collecting ICC/ICJ records...")
    count = 0

    # ICC press releases API
    try:
        r = requests.get("https://www.icc-cpi.int/api/search?types=pressrelease&count=50&lang=en-GB", timeout=20)
        if r.status_code == 200:
            for item in r.json().get("results", []):
                title = item.get("title","")
                body = item.get("body","")[:500]
                date = item.get("date","")
                pilots = []
                txt = (title+body).lower()
                if "afghan" in txt: pilots.append("afghanistan")
                if "iran" in txt: pilots.append("iran_hormuz")
                if not pilots: pilots = ["global"]
                _save(_rec(f"ICC: {title[:50]}", item.get("url","https://icc-cpi.int"),
                    "International","ICC-war-crimes-court",date,"en",pilots,
                    f"ICC: {title}. {body}",
                    notes="ICC Press Release"), "icc_icj")
                count += 1
    except Exception as e: log.error(f"ICC API: {e}")

    searches = [
        ("ICC International Criminal Court Afghanistan war crimes investigation", "afghanistan"),
        ("ICJ International Court Justice Iran United States case", "iran_hormuz"),
        ("ICC prosecutor war crimes charges evidence Afghanistan", "afghanistan"),
        ("ICJ Iran nuclear sanctions international law ruling", "iran_hormuz"),
        ("ICTY ICTR war crimes tribunal precedent law", "both"),
        ("international criminal law command responsibility superior", "both"),
        ("universal jurisdiction war crimes prosecution abroad", "both"),
        ("sanctions regime legality international law challenge", "iran_hormuz"),
    ]
    for q, pilot in searches:
        pilots = ["iran_hormuz","afghanistan"] if pilot=="both" else [pilot]
        count += _save_ia(_ia(q), "ICC/ICJ", "International-criminal-law", pilots, "icc_icj", q)
    log.info(f"ICC/ICJ: {count}")
    return count


def collect_constitutional_texts():
    """
    Constitutions and constitutional history — the governance frameworks
    that succeeded or failed in conflict states.
    Afghan constitutions 1923-2004. Iranian constitutional history.
    The gap between constitutional text and lived reality.
    """
    log.info("Collecting constitutional texts...")
    count = 0
    constitutions = [
        ("Afghanistan Constitution 2004 text democratic", "afghanistan", "Afghan-constitution-2004"),
        ("Afghanistan Constitution 1964 text Zahir Shah monarchy", "afghanistan", "Afghan-constitution-1964"),
        ("Afghanistan Constitution 1977 Daoud republic text", "afghanistan", "Afghan-constitution-1977"),
        ("Iran Constitution 1979 Islamic Republic text velayat", "iran_hormuz", "Iranian-constitution-1979"),
        ("Iran Constitution 1906 Constitutional Revolution Qajar", "iran_hormuz", "Iranian-constitution-1906"),
        ("Taliban IEA governance structure decree basic law", "afghanistan", "Taliban-governance-law"),
        ("Afghanistan loya jirga constitutional proceedings", "afghanistan", "Afghan-loya-jirga-constitution"),
        ("comparative constitution conflict state governance failure", "both", "Comparative-constitution"),
    ]
    for q, pilot, perspective in constitutions:
        pilots = ["iran_hormuz","afghanistan"] if pilot=="both" else [pilot]
        count += _save_ia(_ia(q), "Constitution", perspective, pilots, "constitutions", q)
    log.info(f"Constitutional texts: {count}")
    return count


def collect_human_rights_law():
    """
    Human rights law, international humanitarian law, R2P doctrine.
    The normative framework — and where it has been applied or ignored.
    """
    log.info("Collecting human rights law records...")
    count = 0
    searches = [
        ("Universal Declaration Human Rights text application conflict", "both"),
        ("Convention Against Torture CAT state party compliance", "both"),
        ("International Covenant Civil Political Rights ICCPR war", "both"),
        ("refugee convention 1951 non-refoulement Afghan Iran", "both"),
        ("responsibility to protect R2P doctrine application failure", "both"),
        ("human rights law armed conflict IHL customary law", "both"),
        ("UN Human Rights Council resolution country report", "both"),
        ("human rights defenders persecution conflict zone journalist", "both"),
        ("Iran UPR Universal Periodic Review human rights record", "iran_hormuz"),
        ("Afghanistan UPR Universal Periodic Review Taliban", "afghanistan"),
        ("children rights convention armed conflict recruitment", "both"),
        ("women rights CEDAW war conflict implementation gap", "both"),
    ]
    for q, pilot in searches:
        pilots = ["iran_hormuz","afghanistan"] if pilot=="both" else [pilot]
        count += _save_ia(_ia(q), "Human Rights Law", "International-human-rights-law", pilots, "human_rights_law", q)
    log.info(f"Human rights law: {count}")
    return count


def run_judicial_legal():
    total = 0
    total += collect_icc_icj()
    total += collect_constitutional_texts()
    total += collect_human_rights_law()
    log.info(f"Judicial/legal complete: {total}")
    return total

if __name__ == "__main__":
    run_judicial_legal()
