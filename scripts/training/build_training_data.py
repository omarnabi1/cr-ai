#!/usr/bin/env python3
"""
CR-AI Training Data Builder — Phase 3 Step 1
Converts raw collected records into instruction-response pairs
for fine-tuning Mistral-7B with QLoRA.

Output format: JSONL {"instruction": "...", "input": "...", "response": "..."}
Alpaca format — compatible with MLX-LM and HuggingFace TRL SFTTrainer.

Run: python3 scripts/training/build_training_data.py
"""

import json, logging, random
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR  = Path(__file__).parent.parent.parent
DATA_DIR  = BASE_DIR / "data" / "raw"
TRAIN_DIR = BASE_DIR / "data" / "training"
TRAIN_DIR.mkdir(parents=True, exist_ok=True)

TAXONOMY_PATH = BASE_DIR / "taxonomy" / "taxonomy_v6_meta.json"

# ── System prompt injected into every training example ──────────────────────
SYSTEM_PROMPT = """You are CR-AI, a conflict resolution analysis system built on the \
Conflict Resolution AI taxonomy v6. You analyze geopolitical conflicts using a \
4-thread reasoning architecture: Legal-institutional, Sovereign-civilizational, \
Incentive gap, and Human security. You identify conflict types, structural drivers, \
actor positions, and recommend resolution frameworks from a 9-layer resolution stack. \
You are resolution-oriented, not destruction-oriented. Your analysis is rigorous, \
multi-perspectival, and grounded in evidence."""

# ── Template generators — each produces one training pair ───────────────────

def make_conflict_analysis_pair(record):
    """Generate: given news/event text → conflict analysis"""
    text = record.get("text", "").strip()
    if len(text) < 50:
        return None
    pilot = record.get("pilot_conflicts", ["unknown"])[0]
    perspective = record.get("source_perspective", "unknown")
    source = record.get("source_name", "unknown")
    conflict_name = "Iran-US Hormuz dispute" if "iran" in pilot else "Afghanistan conflict"

    instruction = f"Analyze the following news report about the {conflict_name} using the CR-AI taxonomy. Identify the conflict type, primary structural drivers, actor positions, and recommend an initial resolution pathway."

    input_text = f"Source: {source} ({perspective})\n\n{text[:800]}"

    response = f"""**Conflict Analysis — CR-AI Taxonomy v6**

**Conflict Classification:**
- Primary type: {"Geopolitical-resource/strategic" if "iran" in pilot else "Intrastate-ideological/governance"}
- Pilot conflict: {conflict_name}
- Source perspective: {perspective}

**4-Thread Reasoning:**
1. Legal-institutional: {"International sanctions regime, JCPOA framework violations, UNSC resolutions" if "iran" in pilot else "Doha Agreement implementation gaps, IEA governance legitimacy deficit"}
2. Sovereign-civilizational: {"Iranian revolutionary state identity vs Western liberal order" if "iran" in pilot else "Taliban Deobandi governance vs pluralist Afghan society"}
3. Incentive gap: {"IRGC economic interests in sanctions economy vs civilian population seeking relief" if "iran" in pilot else "Taliban opium revenue vs international aid conditionality"}
4. Human security: {"Iranian civilian population bearing sanctions burden" if "iran" in pilot else "Afghan civilian population under Taliban restrictions, Hazara persecution"}

**Structural Drivers (from registry):**
- {"Resource competition (oil/gas), external power intervention, sanctions leverage" if "iran" in pilot else "Governance vacuum, ethnic-religious marginalization, illicit economy dependency"}

**Resolution Framework Recommendation:**
- {"Track II diplomacy via Oman backchannel, phased sanctions relief for nuclear verification steps" if "iran" in pilot else "Shura/ijma-based intra-Afghan dialogue, conditional recognition framework"}

**Confidence:** Medium — single-source analysis, requires multi-perspective verification."""

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response,
        "metadata": {
            "source": source,
            "pilot": pilot,
            "template": "conflict_analysis",
            "record_id": record.get("id", "")
        }
    }


def make_driver_identification_pair(record):
    """Generate: given event → identify structural drivers"""
    text = record.get("text", "").strip()
    if len(text) < 50:
        return None
    pilot = record.get("pilot_conflicts", ["unknown"])[0]

    instruction = "Identify the structural drivers present in this conflict event using the CR-AI structural driver registry."

    input_text = text[:600]

    drivers_iran = ["external_power_intervention", "resource_competition", "sanctions_leverage", "proxy_network_activation"]
    drivers_afg  = ["governance_vacuum", "ethnic_religious_marginalization", "illicit_economy_dependency", "external_power_withdrawal"]
    drivers = drivers_iran if "iran" in pilot else drivers_afg

    response = f"""**Structural Driver Analysis:**

Active drivers identified in this event:
{chr(10).join(f"- **{d.replace('_',' ').title()}**: Present — evidence in source text" for d in drivers[:3])}

**Driver interaction pattern:** These drivers form a reinforcing loop — {"sanctions increase IRGC leverage over civilian economy, which entrenches hardline positions, which makes sanctions harder to lift" if "iran" in pilot else "governance vacuum enables Taliban consolidation, which accelerates external withdrawal, which deepens the vacuum"}.

**Relapse risk:** {"High — structural drivers are embedded in both state and non-state actor incentives" if "iran" in pilot else "Critical — root drivers unaddressed by Doha Agreement"}

**Required for resolution:** All active structural drivers must be addressed in sequenced order — addressing symptoms without root drivers guarantees relapse."""

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response,
        "metadata": {
            "source": record.get("source_name", ""),
            "pilot": pilot,
            "template": "driver_identification",
            "record_id": record.get("id", "")
        }
    }

def make_actor_position_pair(record):
    """Generate: given event → map actor positions"""
    text = record.get("text", "").strip()
    if len(text) < 50:
        return None
    pilot = record.get("pilot_conflicts", ["unknown"])[0]

    instruction = "Map the actor positions in this conflict event. Distinguish between public stated positions and estimated private interests using the CR-AI actor profile framework."

    input_text = text[:600]

    if "iran" in pilot:
        response = """**Actor Position Mapping:**

**Iran (Islamic Republic):**
- Public position: Sovereign right to nuclear program, sanctions are economic warfare
- Private interests: Regime survival, IRGC economic stake in sanctions economy, sanctions relief for civilian legitimacy
- Position gap: Publicly maximalist, privately flexible on enrichment caps if relief guaranteed
- Spoiler risk: High — IRGC hardliners benefit from no-deal status quo

**United States:**
- Public position: Non-proliferation, regional stability, ally security
- Private interests: Israeli security assurance, domestic political constraints, oil market stability
- Position gap: Executive willing to re-enter modified JCPOA, Congress resistant
- Spoiler risk: Medium — electoral cycle dependency

**Incentive gap:** Both parties have domestic spoilers who benefit from continued conflict. Resolution requires simultaneous face-saving for both leaderships."""
    else:
        response = """**Actor Position Mapping:**

**Taliban (IEA):**
- Public position: Sovereign Islamic governance, no foreign interference
- Private interests: International recognition for sanctions removal, internal factional balance
- Position gap: Haqqani hardliners vs Kandahari pragmatists — not a unified actor
- Spoiler risk: Critical — Haqqani network can veto any deal

**Afghan Civil Society / Hazara:**
- Public position: Right to education, political inclusion, physical security
- Private interests: Survival — emigration as fallback if no protection
- Position gap: Minimal — stated and actual interests aligned
- Spoiler risk: Low — no leverage to spoil, only to suffer

**International Community:**
- Public position: Human rights conditions for recognition
- Private interests: Regional stability, migration control, counter-terrorism
- Position gap: Willing to soften conditions for Taliban engagement in practice"""

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response,
        "metadata": {
            "source": record.get("source_name", ""),
            "pilot": pilot,
            "template": "actor_position",
            "record_id": record.get("id", "")
        }
    }


def make_resolution_framework_pair(record):
    """Generate: given conflict context → recommend resolution frameworks"""
    text = record.get("text", "").strip()
    if len(text) < 50:
        return None
    pilot = record.get("pilot_conflicts", ["unknown"])[0]

    instruction = "Based on this conflict context, recommend specific resolution frameworks from the CR-AI 9-layer resolution stack with justification."

    input_text = text[:600]

    if "iran" in pilot:
        response = """**Resolution Framework Recommendations — Iran/Hormuz:**

**Layer 1 (De-escalation):** Immediate confidence-building measures — naval communication hotlines, IAEA access expansion in exchange for sanctions waivers on humanitarian goods.

**Layer 3 (Negotiation):** Structured phased agreement — Iran caps enrichment at 60%, US provides $X billion in sanctions relief, verified by IAEA quarterly. Oman backchannel as trusted intermediary (proven 2013).

**Layer 5 (Institutional):** Revive JCPOA architecture with a sunset-clause renegotiation — binding verification mechanism, automatic snapback with neutral arbitration (not unilateral US).

**Layer 7 (Structural):** Address IRGC economic interests directly — provide legal economic alternatives that don't require sanctions evasion, reducing their incentive to spoil.

**Non-linear endpoints:** If negotiation fails → containment with humanitarian carveouts. If IRGC spoils deal → targeted sanctions on IRGC specifically, decoupled from civilian economy.

**Islamic ADR overlay:** Shura-based consultation process within Iranian system — reformist clergy can provide religious legitimacy for compromise."""
    else:
        response = """**Resolution Framework Recommendations — Afghanistan:**

**Layer 1 (De-escalation):** Immediate: ceasefire on targeted Hazara killings, ICC monitoring presence, humanitarian corridors.

**Layer 2 (Humanitarian):** Conditional aid framework — Taliban receives $X in humanitarian aid, verified to reach civilian population, not IRGC or opium economy.

**Layer 4 (Power-sharing):** Intra-Afghan dialogue via Shura/ijma format — religiously legitimate for Taliban, inclusive of ethnic minorities. Qatar as venue (established Doha track).

**Layer 6 (Transitional justice):** Truth and documentation process — UNAMA-led, not ICC, to avoid Taliban red-line triggering.

**Layer 8 (Reconciliation):** Long-term: Ubuntu/community reconciliation at provincial level — bottom-up legitimacy building that doesn't depend on Taliban central agreement.

**Buen Vivir overlay:** Recognize indigenous/ethnic community governance structures (Hazara jirgas, Tajik councils) as parallel legitimate governance — reduces single-actor dependency."""

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response,
        "metadata": {
            "source": record.get("source_name", ""),
            "pilot": pilot,
            "template": "resolution_framework",
            "record_id": record.get("id", "")
        }
    }

def make_perspective_comparison_pair(record):
    """Generate: given single-source report → identify perspective bias + counter-narratives"""
    text = record.get("text", "").strip()
    if len(text) < 50:
        return None
    perspective = record.get("source_perspective", "unknown")
    source = record.get("source_name", "unknown")
    pilot = record.get("pilot_conflicts", ["unknown"])[0]

    instruction = f"This report comes from a {perspective} source. Identify the perspective framing, potential biases, and what counter-narratives a complete CR-AI analysis would need to incorporate."

    input_text = f"Source: {source}\n\n{text[:600]}"

    response = f"""**Perspective Analysis — {perspective}:**

**Framing detected:**
- This source presents the conflict through a {perspective} lens
- Likely emphasis: {"Iranian sovereignty, Western aggression framing, sanctions as illegal" if "Iranian" in perspective or "state" in perspective.lower() else "Taliban repression, humanitarian crisis, international community responsibility" if "Afghan" in perspective else "regional stability, great power competition, non-proliferation norms"}

**What this source likely omits:**
- {"Civilian population grievances against Iranian government, IRGC economic predation" if "Iranian-state" in perspective else "Taliban internal pragmatist faction signals, international community aid conditionality failure" if "Afghan" in perspective else "Non-Western actor agency, local population perspectives"}

**Counter-narratives needed for complete analysis:**
1. {"Iranian civil society / opposition perspective" if "Iranian" in perspective else "Afghan civil society / Hazara perspective"}
2. {"US/Western perspective on IRGC threat" if "Iranian" in perspective else "International community perspective on aid conditionality"}
3. {"Regional actors (Gulf states, Saudi, Israel)" if "iran" in pilot else "Regional actors (Pakistan, India, Central Asia)"}

**CR-AI multi-perspectival requirement:** No single-source analysis is sufficient. This record should be triangulated with at least 3 perspectives before any resolution recommendation is made.

**Confidence adjustment:** Single source → reduce confidence from medium to low until corroborated."""

    return {
        "instruction": instruction,
        "input": input_text,
        "response": response,
        "metadata": {
            "source": source,
            "pilot": pilot,
            "template": "perspective_comparison",
            "record_id": record.get("id", "")
        }
    }


# ── Template registry ────────────────────────────────────────────────────────
TEMPLATES = [
    make_conflict_analysis_pair,
    make_driver_identification_pair,
    make_actor_position_pair,
    make_resolution_framework_pair,
    make_perspective_comparison_pair,
]

# Weight templates — analysis and resolution most important
TEMPLATE_WEIGHTS = [3, 2, 2, 3, 1]  # proportional sampling

def load_all_records():
    """Load all JSONL records from data/raw/"""
    records = []
    for jsonl_file in DATA_DIR.rglob("*.jsonl"):
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        if len(rec.get("text", "")) >= 50:
                            records.append(rec)
        except Exception as e:
            log.warning(f"Failed to read {jsonl_file}: {e}")
    log.info(f"Loaded {len(records)} records from {DATA_DIR}")
    return records


def build_training_pairs(records, pairs_per_record=2):
    """Convert records to instruction-response pairs."""
    pairs = []
    skipped = 0

    for record in records:
        # Sample templates weighted by importance
        chosen = random.choices(TEMPLATES, weights=TEMPLATE_WEIGHTS, k=pairs_per_record)
        for template_fn in chosen:
            pair = template_fn(record)
            if pair is None:
                skipped += 1
                continue
            # Format as Mistral chat template
            formatted = {
                "text": f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{pair['instruction']}\n\nContext:\n{pair['input']} [/INST] {pair['response']} </s>",
                "instruction": pair["instruction"],
                "input": pair["input"],
                "response": pair["response"],
                "metadata": pair["metadata"]
            }
            pairs.append(formatted)

    log.info(f"Generated {len(pairs)} training pairs ({skipped} skipped)")
    return pairs


def split_and_save(pairs, train_ratio=0.9):
    """Split into train/validation and save as JSONL."""
    random.shuffle(pairs)
    split = int(len(pairs) * train_ratio)
    train_pairs = pairs[:split]
    val_pairs   = pairs[split:]

    train_path = TRAIN_DIR / "train.jsonl"
    val_path   = TRAIN_DIR / "val.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for p in train_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for p in val_pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    log.info(f"Saved {len(train_pairs)} train pairs → {train_path}")
    log.info(f"Saved {len(val_pairs)} val pairs   → {val_path}")

    # Save stats
    stats = {
        "built_at": datetime.utcnow().isoformat(),
        "total_pairs": len(pairs),
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "source_records": len(pairs) // 2,
        "templates_used": [fn.__name__ for fn in TEMPLATES],
        "train_file": str(train_path),
        "val_file": str(val_path)
    }
    with open(TRAIN_DIR / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    return train_path, val_path, stats


def run():
    log.info("=== CR-AI Training Data Builder ===")
    records = load_all_records()
    if not records:
        log.error("No records found. Run data collection first.")
        return
    pairs = build_training_pairs(records, pairs_per_record=2)
    train_path, val_path, stats = split_and_save(pairs)
    log.info(f"\n{'='*40}")
    log.info(f"Training data ready:")
    log.info(f"  Train: {stats['train_pairs']} pairs")
    log.info(f"  Val:   {stats['val_pairs']} pairs")
    log.info(f"  Total: {stats['total_pairs']} pairs")
    log.info(f"  Files: {train_path.parent}/")
    log.info(f"{'='*40}")
    return stats


if __name__ == "__main__":
    run()
