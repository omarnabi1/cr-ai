#!/usr/bin/env python3
"""
CR-AI Conflict Graph & Scoring Engine
Defines the relationships between conflicts and a multi-dimensional
scoring system that powers both the analysis UI and the strategy game.

Core concepts:
  - ConflictNode: A conflict with a full score vector
  - ConflictEdge: A typed, weighted connection between conflicts
  - ConflictGraph: The full network — queryable, updatable, game-ready

Score dimensions (0-100 each):
  intensity      — active violence level
  stability      — governance/institutional fragility
  resolution     — proximity to a viable deal
  contagion      — spillover risk to neighboring conflicts
  alignment      — actor position convergence
  humanitarian   — civilian suffering index
  economic       — resource/sanction stress
  composite      — weighted average of all dimensions

Game logic translation:
  intensity  → threat level, military unit strength
  stability  → governance actions available per turn
  resolution → peace track progress bar
  contagion  → adjacency effects on connected nodes
  alignment  → diplomatic action costs
  humanitarian → civilian casualty counter, legitimacy loss
  economic   → budget/resource available per turn
  composite  → overall conflict status color (green→red)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

# ── Score Dimensions ──────────────────────────────────────────────────────────

SCORE_WEIGHTS = {
    "intensity":    0.20,
    "stability":    0.15,
    "resolution":   0.20,
    "contagion":    0.10,
    "alignment":    0.10,
    "humanitarian": 0.15,
    "economic":     0.10,
}

INTENSITY_LEVELS = {
    (0,  20):  "dormant",
    (21, 40):  "simmering",
    (41, 60):  "active",
    (61, 80):  "high",
    (81, 100): "critical",
}

def intensity_label(score: int) -> str:
    for (lo, hi), label in INTENSITY_LEVELS.items():
        if lo <= score <= hi:
            return label
    return "unknown"


@dataclass
class ConflictScore:
    """Multi-dimensional score for a single conflict. All values 0-100."""
    intensity:    int = 50   # active violence level
    stability:    int = 50   # governance fragility (higher = more fragile)
    resolution:   int = 50   # proximity to deal (higher = closer)
    contagion:    int = 50   # spillover risk to adjacent conflicts
    alignment:    int = 50   # actor convergence (higher = more aligned)
    humanitarian: int = 50   # civilian suffering (higher = worse)
    economic:     int = 50   # resource/sanction stress (higher = worse)

    @property
    def composite(self) -> int:
        """Weighted composite score — the overall conflict severity."""
        raw = sum(
            getattr(self, dim) * weight
            for dim, weight in SCORE_WEIGHTS.items()
        )
        return round(raw)

    @property
    def status(self) -> str:
        return intensity_label(self.composite)

    @property
    def resolution_proximity(self) -> str:
        if self.resolution >= 70: return "negotiable"
        if self.resolution >= 40: return "distant"
        return "intractable"

    @property
    def game_state(self) -> dict:
        """Translate scores into game mechanics values."""
        return {
            "threat_level":      self.intensity,
            "governance_actions": max(1, round((100 - self.stability) / 20)),
            "peace_track":       self.resolution,
            "spillover_chance":  self.contagion / 100,
            "diplomacy_cost":    round((100 - self.alignment) / 10),
            "civilian_toll":     self.humanitarian,
            "budget_available":  max(0, round((100 - self.economic) * 1.5)),
            "composite":         self.composite,
            "status_color":      self._status_color(),
        }

    def _status_color(self) -> str:
        c = self.composite
        if c < 30: return "#1D9E75"   # green — dormant
        if c < 50: return "#EF9F27"   # amber — simmering
        if c < 70: return "#D85A30"   # coral — active
        return "#E24B4A"              # red — critical

    def to_dict(self) -> dict:
        d = asdict(self)
        d["composite"] = self.composite
        d["status"] = self.status
        d["resolution_proximity"] = self.resolution_proximity
        d["game_state"] = self.game_state
        return d


# ── Edge Types ────────────────────────────────────────────────────────────────

EDGE_TYPES = {
    "proxy_war":          "One conflict is a theater for another's war by proxy",
    "shared_actor":       "Same state/group is active in both conflicts",
    "resource_link":      "Resource flows (oil, drugs, minerals) connect conflicts",
    "ideological":        "Same ideology/movement drives both conflicts",
    "geographic":         "Physical proximity — spillover via borders/refugees",
    "historical_origin":  "One conflict directly caused or spawned the other",
    "diplomatic":         "Resolution of one is prerequisite for the other",
    "economic_dependency":"Sanctions/trade pressure links conflict outcomes",
    "arms_supply":        "Weapons from one conflict's actors feed another",
    "information":        "Propaganda/narrative from one shapes the other",
}


@dataclass
class ConflictEdge:
    """A typed, weighted connection between two conflicts."""
    source_id:    str
    target_id:    str
    edge_type:    str
    weight:       float          # 0.0–1.0 — strength of connection
    direction:    str = "both"   # "source_to_target" | "target_to_source" | "both"
    description:  str = ""
    rca_note:     str = ""       # Root cause analysis implication
    game_effect:  str = ""       # How this edge affects game mechanics
    evidence:     List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Conflict Node ─────────────────────────────────────────────────────────────

@dataclass
class ConflictNode:
    """A conflict with full metadata and scoring."""
    id:           str
    name:         str
    short_name:   str
    region:       str
    actors:       List[str] = field(default_factory=list)
    start_year:   Optional[int] = None
    status:       str = "active"      # active | frozen | resolved | dormant
    score:        ConflictScore = field(default_factory=ConflictScore)
    tags:         List[str] = field(default_factory=list)
    rca_summary:  str = ""
    updated_at:   str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = self.score.to_dict()
        return d


# ── Conflict Graph ────────────────────────────────────────────────────────────

class ConflictGraph:
    """
    The full network of conflicts and their connections.
    Queryable for analysis, serializable for UI/game, updatable by CR-AI model.
    """
    def __init__(self):
        self.nodes: Dict[str, ConflictNode] = {}
        self.edges: List[ConflictEdge] = []

    def add_node(self, node: ConflictNode):
        self.nodes[node.id] = node

    def add_edge(self, edge: ConflictEdge):
        self.edges.append(edge)

    def get_connected(self, conflict_id: str) -> List[Tuple[ConflictNode, ConflictEdge]]:
        """Get all conflicts directly connected to a given conflict."""
        connected = []
        for edge in self.edges:
            if edge.source_id == conflict_id:
                target = self.nodes.get(edge.target_id)
                if target: connected.append((target, edge))
            elif edge.target_id == conflict_id and edge.direction == "both":
                source = self.nodes.get(edge.source_id)
                if source: connected.append((source, edge))
        return connected

    def contagion_impact(self, conflict_id: str) -> Dict[str, float]:
        """
        Calculate how a change in one conflict ripples through the network.
        Used by game engine: if Iran escalates, what changes elsewhere?
        """
        node = self.nodes.get(conflict_id)
        if not node: return {}
        impacts = {}
        for connected_node, edge in self.get_connected(conflict_id):
            base_impact = (node.score.contagion / 100) * edge.weight
            impacts[connected_node.id] = round(base_impact, 3)
        return impacts

    def resolution_prerequisites(self, conflict_id: str) -> List[str]:
        """
        What other conflicts need to move first for this one to resolve?
        Critical for game strategy and real RCA.
        """
        prereqs = []
        for edge in self.edges:
            if edge.target_id == conflict_id and edge.edge_type == "diplomatic":
                prereqs.append(edge.source_id)
        return prereqs

    def to_dict(self) -> dict:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "meta": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "generated_at": datetime.utcnow().isoformat()
            }
        }

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ConflictGraph":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        g = cls()
        for nid, nd in data["nodes"].items():
            score_data = nd.pop("score", {})
            nd.pop("updated_at", None)
            score = ConflictScore(**{
                k: score_data[k] for k in
                ["intensity","stability","resolution","contagion","alignment","humanitarian","economic"]
                if k in score_data
            })
            g.nodes[nid] = ConflictNode(score=score, **{
                k: v for k, v in nd.items()
                if k in ConflictNode.__dataclass_fields__
            })
        for ed in data["edges"]:
            g.edges.append(ConflictEdge(**{
                k: v for k, v in ed.items()
                if k in ConflictEdge.__dataclass_fields__
            }))
        return g


# ── Seed Graph — Pilot Conflicts + Connected Network ─────────────────────────

def build_seed_graph() -> ConflictGraph:
    """
    Build the initial conflict graph with both pilot conflicts and
    all directly connected conflicts. Scores are evidence-based estimates.
    """
    g = ConflictGraph()

    # ── CORE PILOT CONFLICTS ────────────────────────────────────────────────
    g.add_node(ConflictNode(
        id="iran_hormuz", name="Iran / US — Hormuz & Nuclear Dispute",
        short_name="Iran/Hormuz", region="Middle East",
        actors=["Islamic Republic of Iran","United States","IRGC","Israel","Saudi Arabia","EU"],
        start_year=1979, status="active",
        score=ConflictScore(
            intensity=65, stability=72, resolution=35,
            contagion=78, alignment=28, humanitarian=58, economic=82
        ),
        tags=["nuclear","sanctions","proxy","resource","strait"],
        rca_summary="1953 CIA coup destroyed Iranian trust in West. Revolutionary state identity requires anti-Western posture. IRGC economic empire depends on sanctions-era illicit economy. Nuclear program is both deterrence and bargaining chip."
    ))

    g.add_node(ConflictNode(
        id="afghanistan", name="Afghanistan — Taliban / IEA Governance Crisis",
        short_name="Afghanistan", region="Central Asia",
        actors=["Taliban/IEA","Hazara community","Pakistan/ISI","US/NATO","Afghanistan civil society","ISIS-K","Russia","China"],
        start_year=1978, status="active",
        score=ConflictScore(
            intensity=55, stability=91, resolution=22,
            contagion=68, alignment=15, humanitarian=94, economic=88
        ),
        tags=["governance","ethnic","ideology","proxy","humanitarian","narco"],
        rca_summary="1893 Durand Line created illegitimate border. 1979 Soviet invasion destroyed civil society. CIA mujahedeen funding created Taliban precursors. 20yr US occupation failed to build legitimate governance. Opium economy replaced all alternatives."
    ))

    # ── CONNECTED CONFLICTS ─────────────────────────────────────────────────
    g.add_node(ConflictNode(
        id="pakistan_isi", name="Pakistan — Internal / ISI Proxy Strategy",
        short_name="Pakistan/ISI", region="South Asia",
        actors=["Pakistan Army","ISI","PTI","Taliban/TTP","India"],
        start_year=1947, status="active",
        score=ConflictScore(
            intensity=52, stability=74, resolution=30,
            contagion=70, alignment=22, humanitarian=55, economic=65
        ),
        tags=["proxy","nuclear","governance","strategic_depth"],
        rca_summary="Pakistan uses Taliban as strategic depth against India. ISI created and still maintains Taliban networks. Pakistan's own stability is hostage to Afghan stability."
    ))

    g.add_node(ConflictNode(
        id="yemen", name="Yemen — Saudi-Iran Proxy War",
        short_name="Yemen", region="Middle East",
        actors=["Houthi (Iran-backed)","Saudi Arabia/UAE","Yemen government","US","UN"],
        start_year=2014, status="active",
        score=ConflictScore(
            intensity=78, stability=88, resolution=40,
            contagion=60, alignment=32, humanitarian=96, economic=72
        ),
        tags=["proxy","humanitarian","resource","sectarian"],
        rca_summary="Iran funds Houthis as strategic pressure on Saudi southern flank. Yemen is the theater where Iran-Saudi cold war turns hot."
    ))

    g.add_node(ConflictNode(
        id="israel_palestine", name="Israel / Palestine",
        short_name="Israel/Palestine", region="Middle East",
        actors=["Israel","Hamas","Palestinian Authority","Iran","US","Hezbollah","Egypt","Jordan"],
        start_year=1948, status="active",
        score=ConflictScore(
            intensity=88, stability=82, resolution=12,
            contagion=85, alignment=8, humanitarian=90, economic=60
        ),
        tags=["territorial","colonial","proxy","resource","religious"],
        rca_summary="Iran uses Hamas and Hezbollah as pressure valves against Israel. Israel-Palestine resolution is prerequisite for any Iran deal."
    ))

    g.add_node(ConflictNode(
        id="ukraine_russia", name="Ukraine — Russia Invasion",
        short_name="Ukraine/Russia", region="Eastern Europe",
        actors=["Russia","Ukraine","US/NATO","EU","China","Belarus"],
        start_year=2022, status="active",
        score=ConflictScore(
            intensity=90, stability=78, resolution=18,
            contagion=72, alignment=20, humanitarian=82, economic=75
        ),
        tags=["territorial","great_power","proxy","resource","sovereignty"],
        rca_summary="Russia-Ukraine conflict reshapes global arms flows, sanctions architecture, and energy markets — all of which directly affect Iran and Afghanistan."
    ))

    # ── EDGES — how conflicts connect ───────────────────────────────────────

    # Iran ↔ Yemen: direct proxy war
    g.add_edge(ConflictEdge(
        source_id="iran_hormuz", target_id="yemen",
        edge_type="proxy_war", weight=0.85, direction="source_to_target",
        description="Iran funds, arms, and trains Houthi forces as strategic pressure on Saudi Arabia",
        rca_note="Resolving Iran/Hormuz requires addressing Iran's proxy strategy — Yemen is central",
        game_effect="Escalation in Iran raises Houthi attack probability by contagion_score × 0.85",
        evidence=["IRGC Quds Force arms supply routes", "Houthi ballistic missile technology traces to Iran"]
    ))

    # Iran ↔ Israel/Palestine: proxy via Hamas/Hezbollah
    g.add_edge(ConflictEdge(
        source_id="iran_hormuz", target_id="israel_palestine",
        edge_type="proxy_war", weight=0.80, direction="source_to_target",
        description="Iran funds Hamas and Hezbollah as anti-Israel strategic assets",
        rca_note="No Iran nuclear deal possible while Iran-Israel proxy war is unresolved",
        game_effect="Iran deal progress reduces Hamas/Hezbollah funding — affects Israel/Palestine stability",
        evidence=["Hamas October 7 attack planning involved IRGC", "Hezbollah receives $700M/yr from Iran"]
    ))

    # Afghanistan ↔ Pakistan: foundational
    g.add_edge(ConflictEdge(
        source_id="pakistan_isi", target_id="afghanistan",
        edge_type="proxy_war", weight=0.90, direction="both",
        description="Pakistan/ISI created, supported, and still maintains Taliban as strategic depth",
        rca_note="Afghanistan cannot stabilize without Pakistan stopping Taliban sanctuary. Pakistan cannot reform without civilian control of ISI.",
        game_effect="Pakistan stability score directly modifies Afghanistan resolution score by ±0.9",
        evidence=["Quetta Shura Taliban HQ in Pakistan", "ISI payments to Taliban commanders documented"]
    ))

    # Afghanistan ↔ Iran: Hazara/drug/refugee
    g.add_edge(ConflictEdge(
        source_id="iran_hormuz", target_id="afghanistan",
        edge_type="shared_actor", weight=0.55, direction="both",
        description="Iran hosts 3.5M Afghan refugees, supports anti-Taliban Hazara networks, shares drug trade border",
        rca_note="Iran has leverage over Afghanistan Taliban through refugee flows and Hazara support",
        game_effect="Iran stability affects Afghan refugee flows — humanitarian score impact 0.55",
        evidence=["Iran-Taliban border clashes 2023", "Fatemiyoun Brigade (Iran-backed Afghan Shia fighters)"]
    ))

    # Ukraine ↔ Iran: arms supply reversal
    g.add_edge(ConflictEdge(
        source_id="ukraine_russia", target_id="iran_hormuz",
        edge_type="arms_supply", weight=0.70, direction="both",
        description="Russia-Iran arms trade: Iran supplies drones to Russia, Russia provides nuclear/missile tech to Iran",
        rca_note="Ukraine war gives Iran geopolitical leverage — Russia needs Iran, reducing Western pressure effectiveness",
        game_effect="Ukraine escalation raises Iran's strategic value, reduces resolution score by contagion × 0.70",
        evidence=["Shahed drone supplies confirmed", "Russia-Iran strategic partnership 2023"]
    ))

    # Israel/Palestine ↔ Iran: prerequisite link
    g.add_edge(ConflictEdge(
        source_id="israel_palestine", target_id="iran_hormuz",
        edge_type="diplomatic", weight=0.75, direction="source_to_target",
        description="Any Iran nuclear deal requires Israeli security assurances — Israel has effective veto on US-Iran negotiations",
        rca_note="Israel-Palestine resolution is partial prerequisite for Iran deal sustainability",
        game_effect="Israel/Palestine resolution score must reach 40+ before Iran deal can reach 70+",
        evidence=["Israeli lobby opposition to JCPOA", "Netanyahu opposition to Biden Iran negotiations"]
    ))

    return g


# ── Main — build, save, print summary ────────────────────────────────────────

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent
    OUT_PATH = BASE_DIR / "docs" / "conflict_graph.json"

    print("Building CR-AI conflict graph...")
    g = build_seed_graph()
    g.save(str(OUT_PATH))

    print(f"\nGraph saved → {OUT_PATH}")
    print(f"Nodes: {len(g.nodes)}  |  Edges: {len(g.edges)}")

    print("\n── Conflict scores ──")
    for node in g.nodes.values():
        gs = node.score.game_state
        print(f"  {node.short_name:<20} composite={node.score.composite:3d} "
              f"status={node.score.status:<10} peace_track={gs['peace_track']}")

    print("\n── Contagion from Iran/Hormuz ──")
    for nid, impact in g.contagion_impact("iran_hormuz").items():
        print(f"  → {g.nodes[nid].short_name}: {impact:.2f} contagion impact")

    print("\n── Resolution prerequisites for Iran/Hormuz ──")
    prereqs = g.resolution_prerequisites("iran_hormuz")
    for p in prereqs:
        print(f"  Requires: {g.nodes[p].short_name}")
    if not prereqs:
        print("  (none defined yet — add diplomatic edges)")
