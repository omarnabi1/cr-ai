#!/usr/bin/env python3
"""
Philosophy, Ethics & Resolution Theory Collector — CR-AI
Every major tradition of thought on war, peace, justice, and reconciliation.

This is what makes CR-AI different from a news aggregator:
it understands WHY conflicts should be resolved and HOW,
drawing from every human wisdom tradition simultaneously.

Sources:
  - Western political philosophy (Kant, Rousseau, Locke, Hobbes, Rawls)
  - Islamic political philosophy (al-Mawardi, Ibn Rushd, Sayyid Qutb)  
  - African ubuntu philosophy (Tutu, Mandela, post-apartheid reconciliation)
  - Buddhist non-violence (Thich Nhat Hanh, Dalai Lama, engaged Buddhism)
  - Indigenous conflict resolution (Pashtunwali, African palaver, circle justice)
  - Feminist peace theory (Cynthia Enloe, Betty Reardon)
  - Critical theory (Frankfurt School, Gramsci hegemony)
  - Game theory and negotiation science (Nash, Schelling, Fisher)
  - Transitional justice (Minow, Teitel)
  - Restorative justice (Zehr, Braithwaite)
"""

import json, hashlib, logging, requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(str(Path(__file__).parent.parent.parent.parent / "logs" / "philosophy.log")),
              logging.StreamHandler()])
log = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent.parent.parent
OUT = BASE_DIR / "data" / "raw" / "philosophy_ethics"
OUT.mkdir(parents=True, exist_ok=True)

def _rec(sn, url, country, perspective, date, lang, pilots, text, conf="high", notes=""):
    return {"id": hashlib.sha256(f"{sn}{date}{text[:60]}".encode()).hexdigest()[:16],
            "source_name": sn, "source_url": url, "source_country": country,
            "source_perspective": perspective, "date": date, "language": lang,
            "category": "philosophy_ethics", "pilot_conflicts": pilots,
            "conflict_types": [], "text": text[:3000], "confidence": conf,
            "notes": notes, "collected_at": datetime.utcnow().isoformat()}

def _save(rec, sub):
    p = OUT / sub; p.mkdir(exist_ok=True)
    with open(p / f"{sub}.jsonl","a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")

def _ia(q, rows=20):
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={
            "q": q, "fl[]": "identifier,title,description,date,creator",
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
        creator = doc.get("creator","")
        if isinstance(creator,list): creator="; ".join(creator)
        text = f"{doc.get('title','')}. {creator}. {desc[:500]}"
        if len(text)<30: continue
        _save(_rec(f"{prefix}: {doc.get('title','')[:50]}",
            f"https://archive.org/details/{doc.get('identifier','')}",
            "Global", perspective, doc.get("date",""), "en", pilots, text,
            notes=f"Philosophy: {q}"), sub)
        count += 1
    return count

# Gutenberg political philosophy texts
GUTENBERG_PHILOSOPHY = [
    (4280, "Hobbes - Leviathan (state/sovereignty/war)", "UK", "Western-political-philosophy"),
    (7370, "Locke - Two Treatises of Government", "UK", "Western-liberal"),
    (46333,"Rousseau - Social Contract", "France", "Western-social-contract"),
    (5683, "Kant - Perpetual Peace", "Germany", "Kantian-peace-theory"),
    (4363, "Mill - On Liberty", "UK", "Western-liberal"),
    (67858,"Rawls - A Theory of Justice (excerpt)", "USA", "Liberal-justice-theory"),
    (3268, "Grotius - Law of War and Peace", "Netherlands", "International-law-origins"),
    (30, "Dante - De Monarchia (universal peace)", "Italy", "Medieval-peace-theory"),
]


def collect_western_political_philosophy():
    """Hobbes, Locke, Rousseau, Kant, Rawls — foundations of Western conflict theory."""
    log.info("Collecting Western political philosophy...")
    count = 0
    for gid, title, country, perspective in GUTENBERG_PHILOSOPHY:
        try:
            r = requests.get(f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", timeout=20)
            if r.status_code != 200: continue
            text = f"Political philosophy: {title}. " + r.text[:2000].replace("\r\n"," ")
            _save(_rec(title, f"https://www.gutenberg.org/ebooks/{gid}",
                country, perspective, "historical", "en",
                ["iran_hormuz","afghanistan"], text, conf="high",
                notes=f"Gutenberg philosophy #{gid}"), "western_philosophy")
            count += 1
        except Exception as e: log.error(f"Gutenberg {gid}: {e}")

    ia_searches = [
        ("just war theory Augustine Aquinas criteria analysis", "Western-just-war"),
        ("liberal peace theory democracy war Kant perpetual peace", "Liberal-peace"),
        ("realism international relations Morgenthau power conflict", "Realist-IR"),
        ("constructivism identity norms conflict international relations", "Constructivist-IR"),
        ("critical security studies emancipation Booth conflict", "Critical-security"),
        ("feminist security theory gender war peace Tickner", "Feminist-security"),
    ]
    for q, perspective in ia_searches:
        count += _save_ia(_ia(q), "Western Philosophy", perspective,
            ["iran_hormuz","afghanistan"], "western_philosophy", q)
    log.info(f"Western political philosophy: {count}")
    return count


def collect_non_western_philosophy():
    """
    Ubuntu, Buddhist non-violence, Islamic political philosophy,
    Indigenous governance theory, African philosophy of peace.
    """
    log.info("Collecting non-Western philosophy...")
    count = 0
    searches = [
        ("Ubuntu philosophy community reconciliation Africa Tutu", "African", "Ubuntu-philosophy"),
        ("Buddhist non-violence ahimsa engaged Buddhism peace Thich Nhat Hanh", "Buddhist", "Buddhist-peace"),
        ("Dalai Lama Buddhism conflict resolution compassion non-violence", "Tibetan", "Buddhist-peace"),
        ("African philosophy palaver community dialogue conflict resolution", "African", "African-philosophy"),
        ("Confucian harmony social order conflict prevention Chinese", "Chinese", "Confucian-harmony"),
        ("Taoism wu wei non-action conflict resolution Chinese", "Chinese", "Taoist-philosophy"),
        ("Gandhi satyagraha non-violence civil resistance theory", "Indian", "Gandhian-non-violence"),
        ("Sayyid Qutb Islamic political theory Milestones jihad state", "Egyptian", "Islamist-political"),
        ("Ayatollah Khomeini velayat faqih Islamic governance theory", "Iranian", "Iranian-political-theology"),
        ("progressive Islam reform ijtihad democracy reconciliation", "Multiple", "Progressive-Islam"),
        ("Indigenous circle justice restorative healing community", "Indigenous", "Indigenous-restorative"),
        ("Ubuntu restorative justice post-conflict reconciliation Africa", "African", "Ubuntu-justice"),
    ]
    for q, region, perspective in searches:
        count += _save_ia(_ia(q), f"{region} Philosophy", perspective,
            ["iran_hormuz","afghanistan"], "non_western_philosophy", q)
    log.info(f"Non-Western philosophy: {count}")
    return count


def collect_negotiation_game_theory():
    """
    Game theory, negotiation science, mediation theory.
    The SCIENCE of how conflicts end — not ideology, pure mechanics.
    Nash equilibria in conflict. Schelling focal points. Fisher interest-based negotiation.
    """
    log.info("Collecting negotiation and game theory...")
    count = 0
    searches = [
        ("game theory Nash equilibrium conflict strategy international", "Game-theory"),
        ("Schelling focal points coordination game conflict", "Schelling-game-theory"),
        ("Getting to Yes Fisher Ury interest-based negotiation", "Negotiation-science"),
        ("mediation theory practice Bercovitch conflict settlement", "Mediation-theory"),
        ("ripeness theory conflict resolution timing Zartman", "Ripeness-theory"),
        ("spoiler management peace process Stedman analysis", "Spoiler-theory"),
        ("coercive diplomacy compellence deterrence Schelling Byman", "Coercive-diplomacy"),
        ("Track II diplomacy back channel negotiation unofficial", "Track-II-diplomacy"),
        ("conflict transformation Lederach peacebuilding theory", "Conflict-transformation"),
        ("power mediation third party intervention analysis", "Mediation-power"),
        ("bargaining war Fearon rationalist explanation conflict", "Rationalist-war-theory"),
        ("prisoner dilemma cooperation defection arms race", "Game-theory-arms"),
    ]
    for q, perspective in searches:
        count += _save_ia(_ia(q), "Negotiation/Game Theory", perspective,
            ["iran_hormuz","afghanistan"], "negotiation_game_theory", q)
    log.info(f"Negotiation/game theory: {count}")
    return count


def collect_transitional_justice():
    """
    Truth and reconciliation, transitional justice, post-conflict healing.
    South Africa TRC. Rwanda Gacaca courts. East Timor CAVR.
    The evidence base for what actually works after violence ends.
    """
    log.info("Collecting transitional justice records...")
    count = 0
    searches = [
        ("South Africa Truth Reconciliation Commission TRC testimony", "African-TRC"),
        ("Rwanda Gacaca courts genocide reconciliation community", "Rwanda-Gacaca"),
        ("truth commission transitional justice truth telling", "Transitional-justice"),
        ("lustration vetting post-conflict accountability perpetrator", "Accountability-justice"),
        ("reparations conflict victims compensation acknowledgment", "Reparations-theory"),
        ("amnesty forgiveness justice peace trade-off transitional", "Amnesty-peace"),
        ("post-conflict reconstruction statebuilding institution", "Post-conflict-rebuild"),
        ("memorialization memory conflict collective trauma healing", "Collective-memory"),
        ("Colombia peace process FARC transitional justice model", "Colombia-peace"),
        ("Northern Ireland Good Friday Agreement reconciliation", "Northern-Ireland-peace"),
        ("Timor-Leste CAVR truth commission atrocity documentation", "Timor-peace"),
        ("Afghanistan transitional justice reconciliation mechanism", "Afghan-TJ"),
    ]
    for q, perspective in searches:
        count += _save_ia(_ia(q), "Transitional Justice", perspective,
            ["iran_hormuz","afghanistan"], "transitional_justice", q)
    log.info(f"Transitional justice: {count}")
    return count


def run_philosophy_ethics():
    total = 0
    total += collect_western_political_philosophy()
    total += collect_non_western_philosophy()
    total += collect_negotiation_game_theory()
    total += collect_transitional_justice()
    log.info(f"Philosophy/ethics complete: {total}")
    return total

if __name__ == "__main__":
    run_philosophy_ethics()
