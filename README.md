# Conflict Resolution AI

**Mission:** Purpose-built LLM for geopolitical conflict analysis and resolution.
Same analytical rigor as Palantir/Maven — transparent, open, oriented toward resolution.

**Taxonomy:** v6 — 23 categories, 90+ sub-types, 4-thread reasoning, 9-layer resolution stack
**Pilot conflicts:** Iran / Strait of Hormuz · Afghanistan 2001–2021

---

## Phase progress

- [x] Phase 1 Task 1 — Conflict taxonomy v6 complete
- [x] Phase 1 Task 2 — Dataset registry mapped
- [ ] Phase 1 Task 3 — Choose base model (Llama 3 70B recommended)
- [ ] Phase 1 Task 4 — Set up local hardware (Mac mini M4 Pro)
- [ ] Phase 1 Task 5 — Data ingestion pipeline
- [ ] Phase 1 Task 6 — Actor profile schema
- [ ] Phase 2 — Dataset collection (Iran/Hormuz + Afghanistan)
- [ ] Phase 3 — Model training and validation
- [ ] Phase 4 — Platform and public release

---

## Directory structure

```
CR-AI/
├── data/raw/           # Raw collected documents (never modified)
├── data/processed/     # Cleaned, translated, deduplicated
├── data/datasets/      # Final JSONL training datasets
├── pilots/             # Pilot conflict analysis files
├── scripts/            # Collection, processing, translation, sentiment
├── models/             # Fine-tuned model checkpoints
├── taxonomy/           # Conflict taxonomy v6 JSON
├── docs/               # Documentation and notes
├── logs/               # Collection and processing logs
└── outputs/            # Analysis outputs and reports
```
