#!/usr/bin/env python3
"""
Religious Texts Collector — CR-AI Phase 2
Sources: Quran (free API), Hadith collections, contemporary Islamic scholarship,
         Buddhist texts (for reference), open-access theology archives.

These feed the Islamic ADR, Shura/ijma, and Ubuntu resolution frameworks in taxonomy v6.
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(Path(__file__).parent.parent.parent / "logs" / "religious.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

OUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw" / "religious_texts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Quran chapters most relevant to justice, conflict, peace, governance
QURAN_CHAPTERS = [
    {"surah": 2,  "name": "Al-Baqarah",    "theme": "justice_governance"},
    {"surah": 4,  "name": "An-Nisa",        "theme": "justice_rights"},
    {"surah": 5,  "name": "Al-Maidah",      "theme": "law_covenant"},
    {"surah": 8,  "name": "Al-Anfal",       "theme": "conflict_resolution"},
    {"surah": 9,  "name": "At-Tawbah",      "theme": "treaties_conflict"},
    {"surah": 49, "name": "Al-Hujurat",     "theme": "reconciliation_community"},
    {"surah": 60, "name": "Al-Mumtahanah",  "theme": "relations_nonbelievers"},
]

def collect_quran():
    """Collect Quran verses via free API — no key needed."""
    log.info("Collecting Quran verses relevant to conflict/justice/peace...")
    count = 0
    out_path = OUT_DIR / "quran_conflict_justice.jsonl"

    for chapter in QURAN_CHAPTERS:
        try:
            # alquran.cloud API — free, no auth
            resp = requests.get(
                f"https://api.alquran.cloud/v1/surah/{chapter['surah']}/en.asad",
                timeout=15
            )
            if resp.status_code != 200:
                log.warning(f"Quran API surah {chapter['surah']}: HTTP {resp.status_code}")
                continue
            data = resp.json().get("data", {})
            ayahs = data.get("ayahs", [])
            log.info(f"  Surah {chapter['surah']} ({chapter['name']}): {len(ayahs)} verses")

            for ayah in ayahs:
                text = ayah.get("text", "")
                if len(text) < 20:
                    continue
                rec = {
                    "id": hashlib.sha256(f"quran_{chapter['surah']}_{ayah.get('numberInSurah',0)}".encode()).hexdigest()[:16],
                    "source_name": "Quran",
                    "source_url": "https://quran.com",
                    "source_country": "Global",
                    "source_perspective": "Islamic-scripture",
                    "date": "610-632 CE",
                    "language": "en",
                    "category": "religious_texts",
                    "pilot_conflicts": ["iran_hormuz", "afghanistan"],
                    "conflict_types": [],
                    "text": f"Quran {chapter['surah']}:{ayah.get('numberInSurah','')} ({chapter['name']}) — {text}",
                    "surah": chapter["surah"],
                    "surah_name": chapter["name"],
                    "ayah": ayah.get("numberInSurah", 0),
                    "theme": chapter["theme"],
                    "resolution_framework": "Islamic_ADR",
                    "translation": "Asad",
                    "confidence": "high",
                    "notes": "Quran verses relevant to conflict resolution, justice, governance",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"Quran surah {chapter['surah']}: {e}")

    log.info(f"Quran collection: {count} verses")
    return count

def collect_hadith():
    """Collect Hadith collections via HadithAPI.com — free, no key."""
    log.info("Collecting Hadith on justice, governance, conflict...")
    count = 0
    out_path = OUT_DIR / "hadith_conflict_justice.jsonl"

    # Search terms relevant to conflict resolution
    search_terms = [
        "justice", "peace", "reconciliation", "governance",
        "oppression", "rights", "war", "treaty", "arbitration"
    ]

    for term in search_terms:
        try:
            resp = requests.get(
                f"https://hadithapi.com/api/hadiths/?apikey=$2y$10$WlDsJjYs5QHLv1OzKdOzLuJ5BQb3b",
                params={"headingEn": term, "limit": 20},
                timeout=15
            )
            # Fallback: use sunnah.com API structure
            resp2 = requests.get(
                "https://api.sunnah.com/v1/search",
                params={"q": term, "limit": 20},
                headers={"X-API-Key": "SqD712P3E82xnwOAEOkGd5JZH8s9wRNjuHrO1ZosAoEjyyaArSoKL"},
                timeout=15
            )
            if resp2.status_code == 200:
                results = resp2.json().get("data", [])
                for h in results:
                    text = h.get("body", h.get("text", ""))
                    if len(text) < 30:
                        continue
                    rec = {
                        "id": hashlib.sha256(f"hadith_{term}_{text[:40]}".encode()).hexdigest()[:16],
                        "source_name": f"Hadith — {h.get('collection', 'Sunnah')}",
                        "source_url": "https://sunnah.com",
                        "source_country": "Global",
                        "source_perspective": "Islamic-hadith",
                        "date": "600-900 CE",
                        "language": "en",
                        "category": "religious_texts",
                        "pilot_conflicts": ["iran_hormuz", "afghanistan"],
                        "conflict_types": [],
                        "text": f"{h.get('collection','')}: {text[:800]}",
                        "collection": h.get("collection", ""),
                        "book": h.get("book", ""),
                        "theme": term,
                        "resolution_framework": "Islamic_ADR",
                        "confidence": "high",
                        "notes": f"Hadith search: '{term}'",
                        "collected_at": datetime.utcnow().isoformat()
                    }
                    with open(out_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    count += 1
        except Exception as e:
            log.error(f"Hadith '{term}': {e}")

    log.info(f"Hadith collection: {count} records")
    return count

def collect_contemporary_islamic_scholarship():
    """
    Collect contemporary Islamic ADR and governance scholarship via IA.
    Targets fatawa, shura council decisions, and Islamic legal opinions
    on conflict, arbitration, and peace.
    """
    log.info("Collecting contemporary Islamic scholarship from Internet Archive...")
    count = 0
    out_path = OUT_DIR / "islamic_scholarship.jsonl"

    searches = [
        "Islamic arbitration conflict resolution sharia",
        "shura council governance Islam",
        "fatwa peace treaty Islam",
        "Islamic law war peace jihad",
        "Muslim mediation reconciliation",
    ]

    for q in searches:
        try:
            resp = requests.get(
                "https://archive.org/advancedsearch.php",
                params={"q": q, "fl[]": "identifier,title,description,date,creator",
                        "rows": 20, "output": "json"},
                timeout=15
            )
            if resp.status_code != 200:
                continue
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                desc = doc.get("description", "")
                if isinstance(desc, list): desc = " ".join(desc)
                text = f"{doc.get('title','')}. {desc[:600]}"
                if len(text) < 30: continue
                rec = {
                    "id": hashlib.sha256(doc.get("identifier","").encode()).hexdigest()[:16],
                    "source_name": f"IA: {doc.get('creator', doc.get('title',''))[:50]}",
                    "source_url": f"https://archive.org/details/{doc.get('identifier','')}",
                    "source_country": "Global",
                    "source_perspective": "Islamic-scholarship",
                    "date": doc.get("date", ""),
                    "language": "en",
                    "category": "religious_texts",
                    "pilot_conflicts": ["iran_hormuz", "afghanistan"],
                    "conflict_types": [],
                    "text": text,
                    "resolution_framework": "Islamic_ADR",
                    "confidence": "medium",
                    "notes": f"Internet Archive: '{q}'",
                    "collected_at": datetime.utcnow().isoformat()
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
        except Exception as e:
            log.error(f"Islamic scholarship '{q}': {e}")

    log.info(f"Islamic scholarship: {count} records")
    return count

def run_religious_collection():
    total = 0
    total += collect_quran()
    total += collect_hadith()
    total += collect_contemporary_islamic_scholarship()
    log.info(f"Religious texts collection complete: {total} total records")
    return total

if __name__ == "__main__":
    run_religious_collection()
