#!/usr/bin/env python3
"""
Actor Profile Schema — CR-AI Phase 1 Task 6
Defines the data structure for conflict actors (states, armed groups,
institutions, individuals) with public vs private position tracking.

Every conflict analysis record references actors from this registry.
"""

import json
from pathlib import Path
from datetime import datetime

SCHEMA_DIR = Path(__file__).parent.parent / "docs"
SCHEMA_DIR.mkdir(exist_ok=True)

# ─── ACTOR PROFILE SCHEMA ────────────────────────────────────────────────────

ACTOR_SCHEMA = {
    "schema_version": "1.0",
    "created_at": datetime.utcnow().isoformat(),
    "description": "CR-AI actor profile schema for conflict analysis",
    "actor": {
        "id": "str — unique identifier e.g. actor_iran_gov",
        "name": "str — canonical name",
        "aliases": ["str — alternate names, abbreviations"],
        "actor_type": [
            "state_government", "armed_non_state", "international_org",
            "regional_org", "political_party", "militia", "terrorist_org",
            "civil_society", "corporate", "individual_leader", "diaspora_group"
        ],
        "country_of_origin": "ISO 3166-1 alpha-3",
        "primary_conflict_role": [
            "primary_party", "secondary_party", "mediator",
            "spoiler", "guarantor", "proxy", "bystander"
        ],
        "pilot_conflicts": ["iran_hormuz", "afghanistan"],
        "background": {
            "founding_year": "int or null",
            "ideology": ["str — e.g. Shia_Islamist, Pashtun_nationalism, secular_nationalist"],
            "organizational_structure": "str",
            "estimated_strength": "str — e.g. 350,000 active military",
            "funding_sources": ["str"],
            "international_sponsors": ["str — actor IDs"]
        },
        "positions": {
            "description": "Public vs private position tracking — core to CR-AI analysis",
            "public_position": {
                "stated_goals": ["str"],
                "red_lines": ["str — publicly declared non-negotiables"],
                "stated_grievances": ["str"],
                "official_narrative": "str",
                "last_updated": "ISO datetime",
                "sources": ["str — URLs or source IDs"]
            },
            "private_position": {
                "estimated_actual_goals": ["str"],
                "known_flexibilities": ["str — areas where actor may compromise"],
                "internal_factions": ["str — internal divisions affecting position"],
                "backchannel_signals": ["str — known informal communications"],
                "confidence_level": ["low", "medium", "high"],
                "analyst_notes": "str",
                "last_updated": "ISO datetime"
            },
            "position_gap_analysis": "str — narrative of public vs private divergence"
        },
        "incentive_structure": {
            "core_interests": ["str — fundamental needs driving behavior"],
            "economic_incentives": ["str"],
            "security_incentives": ["str"],
            "political_incentives": ["str"],
            "cultural_religious_incentives": ["str"],
            "disincentives_to_peace": ["str — what actor loses if conflict resolves"],
            "spoiler_risk": ["low", "medium", "high", "critical"]
        },
        "relationships": {
            "allies": [{"actor_id": "str", "relationship_type": "str", "strength": "str"}],
            "adversaries": [{"actor_id": "str", "relationship_type": "str", "intensity": "str"}],
            "historical_agreements": [{"name": "str", "year": "int", "status": "str"}]
        },
        "population_sentiment": {
            "domestic_support_level": ["very_low", "low", "moderate", "high", "very_high"],
            "support_trend": ["declining", "stable", "growing"],
            "key_grievances_of_constituents": ["str"],
            "legitimacy_basis": ["electoral", "religious", "military", "traditional", "performance"],
            "sources": ["str"]
        },
        "conflict_history": {
            "previous_conflicts": ["str — brief descriptions"],
            "negotiation_track_record": "str",
            "ceasefire_violations": "int or null",
            "peace_agreement_adherence": "str"
        },
        "metadata": {
            "data_quality": ["low", "medium", "high"],
            "last_reviewed": "ISO datetime",
            "contributing_analysts": ["str"],
            "open_questions": ["str"]
        }
    }
}

# ─── SEED ACTOR PROFILES for both pilot conflicts ────────────────────────────

SEED_ACTORS = [
    # ── IRAN / HORMUZ PILOT ──────────────────────────────────────────────────
    {
        "id": "actor_iran_gov",
        "name": "Islamic Republic of Iran",
        "aliases": ["IRI", "Iranian Government", "Tehran"],
        "actor_type": "state_government",
        "country_of_origin": "IRN",
        "primary_conflict_role": "primary_party",
        "pilot_conflicts": ["iran_hormuz"],
        "background": {
            "founding_year": 1979,
            "ideology": ["Shia_Islamist", "anti-Western", "revolutionary"],
            "organizational_structure": "Theocratic republic with Supreme Leader",
            "estimated_strength": "350,000 active military + 190,000 IRGC",
            "funding_sources": ["oil_exports", "petrochemicals", "proxy_network_taxation"],
            "international_sponsors": []
        },
        "positions": {
            "public_position": {
                "stated_goals": ["End US sanctions", "Regional hegemony", "Nuclear sovereignty"],
                "red_lines": ["No dismantlement of nuclear program", "No regime change"],
                "stated_grievances": ["US sanctions are economic warfare", "Western double standards"],
                "official_narrative": "Iran resists imperial aggression and defends Muslim world"
            },
            "private_position": {
                "estimated_actual_goals": ["Sanctions relief for economic stability", "Regime survival", "IRGC economic interests protected"],
                "known_flexibilities": ["Nuclear enrichment caps if sanctions lifted", "Regional de-escalation deals"],
                "internal_factions": ["Hardliners (Khamenei/IRGC) vs pragmatists (Rouhani-era)"],
                "confidence_level": "medium"
            }
        },
        "incentive_structure": {
            "core_interests": ["Regime survival", "Sanctions removal", "Regional influence"],
            "economic_incentives": ["Oil export revenue", "Sanctions relief worth $50B+/yr"],
            "security_incentives": ["Nuclear deterrence", "Proxy network as strategic depth"],
            "disincentives_to_peace": ["IRGC business empire depends on conflict economy", "Hardliner political power tied to anti-Western narrative"],
            "spoiler_risk": "high"
        },
        "population_sentiment": {
            "domestic_support_level": "low",
            "support_trend": "declining",
            "key_grievances_of_constituents": ["Economic hardship from sanctions", "Corruption", "Political repression"],
            "legitimacy_basis": ["religious", "military"]
        }
    },
    {
        "id": "actor_usa_gov",
        "name": "United States Government",
        "aliases": ["US", "Washington", "State Department"],
        "actor_type": "state_government",
        "country_of_origin": "USA",
        "primary_conflict_role": "primary_party",
        "pilot_conflicts": ["iran_hormuz"],
        "background": {
            "ideology": ["liberal_internationalism", "non-proliferation"],
            "estimated_strength": "1.3M active military, global naval presence"
        },
        "positions": {
            "public_position": {
                "stated_goals": ["Prevent Iranian nuclear weapon", "Protect shipping lanes", "Regional stability"],
                "red_lines": ["No Iranian nuclear weapon", "No Hormuz closure"],
                "stated_grievances": ["Iranian proxy attacks on US forces", "Support for terrorism"]
            },
            "private_position": {
                "estimated_actual_goals": ["Maintain regional order", "Israel security", "Oil price stability"],
                "known_flexibilities": ["Willing to re-enter modified JCPOA", "Sanctions waivers for allies"],
                "confidence_level": "medium"
            }
        },
        "incentive_structure": {
            "core_interests": ["Non-proliferation", "Ally security", "Energy market stability"],
            "disincentives_to_peace": ["Defense contractor lobby", "Israeli opposition to deal"],
            "spoiler_risk": "medium"
        }
    },
    # ── AFGHANISTAN PILOT ────────────────────────────────────────────────────
    {
        "id": "actor_taliban",
        "name": "Islamic Emirate of Afghanistan (Taliban)",
        "aliases": ["Taliban", "IEA", "Taleban"],
        "actor_type": "state_government",
        "country_of_origin": "AFG",
        "primary_conflict_role": "primary_party",
        "pilot_conflicts": ["afghanistan"],
        "background": {
            "founding_year": 1994,
            "ideology": ["Deobandi_Islamism", "Pashtun_nationalism", "anti-Western"],
            "organizational_structure": "Theocratic emirate, shura-based decision making",
            "estimated_strength": "75,000-100,000 fighters",
            "funding_sources": ["opium_trade", "taxation", "Pakistan_ISI_historical", "mining"],
            "international_sponsors": ["Pakistan (historical)", "Qatar (diplomatic)"]
        },
        "positions": {
            "public_position": {
                "stated_goals": ["Islamic governance", "Sovereignty", "International recognition"],
                "red_lines": ["No foreign military presence", "Sharia law non-negotiable"],
                "official_narrative": "Liberated Afghanistan from Western occupation"
            },
            "private_position": {
                "estimated_actual_goals": ["International recognition for economic aid", "Divided internally on women rights pragmatism"],
                "known_flexibilities": ["Girls education possibly negotiable for recognition"],
                "internal_factions": ["Haqqani network hardliners vs Kandahari pragmatists"],
                "confidence_level": "low"
            }
        },
        "incentive_structure": {
            "core_interests": ["International recognition", "Sanctions removal", "Economic survival"],
            "disincentives_to_peace": ["Opium economy disrupted by eradication deals", "Haqqani hardliners resist any compromise"],
            "spoiler_risk": "critical"
        },
        "population_sentiment": {
            "domestic_support_level": "low",
            "support_trend": "declining",
            "key_grievances_of_constituents": ["Economic collapse", "Women oppression", "Ethnic discrimination against Hazara"],
            "legitimacy_basis": ["military", "religious"]
        }
    },
    {
        "id": "actor_hazara_community",
        "name": "Hazara People of Afghanistan",
        "aliases": ["Hazaras", "Hazara minority"],
        "actor_type": "civil_society",
        "country_of_origin": "AFG",
        "primary_conflict_role": "secondary_party",
        "pilot_conflicts": ["afghanistan"],
        "background": {
            "ideology": ["Shia_Islam", "minority_rights", "secular_education"],
            "estimated_strength": "~4-5 million people (20% of population)",
            "funding_sources": ["diaspora_remittances", "Iran_support_historical"]
        },
        "positions": {
            "public_position": {
                "stated_goals": ["Physical security", "Right to education", "Political representation"],
                "red_lines": ["No ethnic cleansing", "No exclusion from governance"],
                "stated_grievances": ["Systematic persecution by Taliban", "Historical massacres (1998 Mazar-i-Sharif)"]
            },
            "private_position": {
                "estimated_actual_goals": ["Survival and emigration as fallback", "International protection"],
                "confidence_level": "medium"
            }
        },
        "incentive_structure": {
            "core_interests": ["Physical survival", "Education access", "Political inclusion"],
            "spoiler_risk": "low"
        },
        "population_sentiment": {
            "domestic_support_level": "very_low",
            "support_trend": "declining",
            "key_grievances_of_constituents": ["Targeted killings by ISIS-K and Taliban", "Displacement"]
        }
    }
]

def save_actor_profiles():
    """Save actor profiles as JSONL to data/raw/actor_profiles/"""
    out_dir = Path(__file__).parent.parent / "data" / "raw" / "actor_profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "seed_actors.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for actor in SEED_ACTORS:
            f.write(json.dumps(actor, ensure_ascii=False) + "\n")
    print(f"Saved {len(SEED_ACTORS)} actor profiles → {out_path}")

    schema_path = SCHEMA_DIR / "actor_profile_schema.json"
    with open(schema_path, "w") as f:
        json.dump(ACTOR_SCHEMA, f, indent=2)
    print(f"Saved schema → {schema_path}")

if __name__ == "__main__":
    save_actor_profiles()
    print(f"\nSchema fields: {list(ACTOR_SCHEMA['actor'].keys())}")
    print(f"Seed actors: {[a['id'] for a in SEED_ACTORS]}")
