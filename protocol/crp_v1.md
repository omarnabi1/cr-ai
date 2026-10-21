# CR-AI Reasoning Protocol (CRP) v1

The standardized procedure CR-AI follows for **any** conflict. The fine-tuned model is trained to produce this exact structure; the eval suite grades against it. Built on taxonomy v6 (23 types, 4 reasoning threads, 9-layer resolution stack) and system prompt v2 ("the alien perspective").

Design rules:
1. **Same steps, every conflict.** A border war, a sectarian insurgency, a labor dispute and a water-rights fight all go through the same ten steps. Only the content changes.
2. **Evidence before judgment.** Every factual claim carries an evidence tier and a source id. Reconstructions are allowed only in their own tier and are never cited as evidence.
3. **Symmetry is testable.** Each actor gets the same fields, filled with the same depth. The eval suite swaps actor labels and checks the reasoning doesn't change (see "Objectivity tests").
4. **Probabilities, not adjectives.** Forecasts and resolution likelihoods are numbers with a time window, so they can be scored later.

## The ten steps

| # | Step | Output | Taxonomy v6 hook |
|---|------|--------|------------------|
| 1 | **Scope** | Conflict instance: actors, geography, time-bounded phase, as-of date | `unit_of_analysis`, `phase_tag` |
| 2 | **Classify** | Primary type + subtypes (from the 23), ontological kind, intensity vector | `conflict_type`, `intensity_vector` |
| 3 | **Map actors** | Every actor with role, authority basis, public position, private position (estimated), red lines, flexibilities, internal factions, spoiler risk | actor profile schema |
| 4 | **Weigh the evidence** | Per actor: coverage count by tier (primary / secondary / reconstructed), languages, gaps | coverage gauge |
| 5 | **Contested claims** | Each disputed fact with every side's version and the evidence for each; marked unresolved unless the evidence settles it | principle 3 |
| 6 | **Root-cause chain** | Consequence chain from structural conditions to today's trigger; ends in conditions, never in a villain | `structural_driver_registry`, principle 5 |
| 7 | **Four threads** | Legal-institutional, sovereign-civilizational, incentive gap, human security, each reasoned separately before they are compared | `reasoning_threads` |
| 8 | **Ripeness** | Is there a mutually hurting stalemate? A way out each side can sell at home? What is missing? | resolution stack layer 1 |
| 9 | **Resolution pathways** | 2 to 4 pathways, each mapped through the 9-layer stack, with prerequisites, sequencing, who must move first, which resolution framework fits these parties (of the 20), and relapse risks | `resolution_stack`, 20 frameworks |
| 10 | **Forecasts** | 3 to 5 resolvable questions with probabilities and dates | Oracle League |

## Output schema (abridged; full JSON Schema in `crp_v1.schema.json`)

```json
{
  "as_of": "YYYY-MM-DD",
  "scope": { "name": "", "actors": [], "geography": "", "phase": "" },
  "classification": { "primary_type": "", "subtypes": [], "kind": "sc|ar|me|co", "intensity": { "lethality": 0, "duration": 0, "displacement": 0, "spillover": 0, "institutional_damage": 0 } },
  "actors": [{ "id": "", "role": "", "authority_basis": "", "public_position": "", "private_position": "", "red_lines": [], "flexibilities": [], "factions": [], "spoiler_risk": "low|medium|high|critical", "evidence": { "primary": 0, "secondary": 0, "reconstructed": 0, "languages": [] } }],
  "contested_claims": [{ "claim": "", "versions": [{ "actor": "", "version": "", "sources": [] }], "status": "unresolved|settled" }],
  "root_cause_chain": [{ "step": "", "period": "", "driver": "", "sources": [] }],
  "threads": { "legal_institutional": "", "sovereign_civilizational": "", "incentive_gap": "", "human_security": "" },
  "ripeness": { "hurting_stalemate": 0.0, "way_out": "", "missing": [] },
  "pathways": [{ "name": "", "framework": "", "layers": [], "prerequisites": [], "first_movers": [], "relapse_risks": [], "probability_12m": 0.0 }],
  "forecasts": [{ "question": "", "resolves_by": "YYYY-MM-DD", "p": 0.0 }],
  "claims": [{ "text": "", "tier": "primary|secondary|reconstructed", "source_ids": [] }]
}
```

## How the model gets trained on it

1. **Breadth first.** Generalizing to any conflict needs many conflicts, not two. Seed set: about 150 conflict instances drawn from UCDP and the PA-X peace agreements database, deliberately including conflicts that *ended* (Northern Ireland, Aceh, Colombia, Mozambique, Bougainville, Sierra Leone) so the model learns how resolution actually happens, plus non-state and sub-state disputes.
2. **Teacher traces.** A frontier model with retrieval over the CR-AI dataset writes CRP analyses as of a fixed date, citing source ids. Every trace passes automatic checks (schema valid, every claim cited, cited text supports the claim, all actors filled to the same depth) and a second-model critique, the same multi-model review loop used for taxonomy v6. Omar reviews a sample.
3. **Fine-tune.** QLoRA on an open 7 to 14B model with 5,000 to 10,000 checked traces. The old templated pairs are retired: they repeated two fixed analyses regardless of input and would have taught the model to ignore the evidence.
4. **Distill, then specialize.** The trained model runs Envoy, Oracle League and the API once it beats its base model on the eval suite.

## Objectivity tests (the eval suite)

- **Symmetry swap:** swap actor names and sides in a scenario; a non-partisan model's reasoning and pathway rankings should mirror. Score = consistency.
- **Source-flip:** give the same events through one side's sources, then the other's. Conclusions should converge on the facts and diverge only on contested claims, which must be labeled.
- **Backtest:** analyses written as of a past date (e.g. Colombia 2012, Aceh 2004) scored against what happened next.
- **Held-out conflicts:** conflicts never seen in training, to measure whether the protocol generalizes.
- **Citation faithfulness:** does the cited document actually say that?
- **Protocol adherence:** all ten steps present, every actor filled to equal depth.
- **Forecast calibration:** Brier score on resolved questions.
