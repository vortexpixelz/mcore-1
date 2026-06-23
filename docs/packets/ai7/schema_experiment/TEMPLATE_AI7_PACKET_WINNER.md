---
template_id: AI7_PACKET_WINNER_TEMPLATE
schema_id: B_research_ledger_hybrid
schema_version: 0.2
packet_version: 0.1
status: active
derived_from_experiment: AI7_SCHEMA_SELECTION_2026_06
date_updated: 2026-06-23
---

# AI7 Packet Winner Template

## Winning schema

Schema B: Research Ledger Packet — hybrid with Schema C claim-tier labels and Schema C sentence field.

Experiment: `AI7_SCHEMA_SELECTION_2026_06` scored four schemas against Bundle 1.
Schema B produced the best average score (7.9/10) and the highest claim_discipline
and reuse_potential scores. This template incorporates two modifications from Schema C.

## Fields

```yaml
schema_id: B_research_ledger_hybrid
schema_version: 0.2
packet_version:         # increment per packet; tracks the creature, not the mold
status:                 # raw_capture | in_progress | filled | reviewed
source_bundle:
date_filled:

summary:                # ONE SENTENCE. The current state and next action in plain language.

observation:            # Direct receipts, measurements, files, test outputs, citations.
                        # No interpretation. Verified only.

interpretation:         # Reasonable reading of the observations. Hedged language.
                        # "Suggests", "is consistent with", "may indicate".

hypothesis:             # Testable claim derived from interpretation.
                        # Must include falsification condition.

evidence_receipts:      # Tier-labeled list. Required tiers:
                        # [ESTABLISHED] - proven by committed code, test, or direct fetch
                        # [PLAUSIBLE]   - supported by observations, not independently validated
                        # [CONJECTURAL] - directional hypothesis, not yet testable
                        # [FORBIDDEN]   - do not use externally until evidence improves

falsification_test:     # What observation would disconfirm the hypothesis?
                        # Be specific: metric, threshold, dataset, model family.

next_action:            # EXACTLY ONE action. Concrete. Scoped. Directly testable.
                        # Must move at least one item from a lower tier to a higher tier,
                        # or produce a repo artifact that does not yet exist.
```

## Required claim discipline

Every future packet must separate:

- **Observed receipts**: direct measurements, committed code, direct-fetched files.
  No vibes. No paraphrases of chat. Cite repo path and SHA or equivalent.
- **Plausible interpretation**: reasonable reading of observed receipts.
  Hedged language required. Cannot be used in external claims without upgrade.
- **Speculative extension**: interesting hypothesis, not yet tested.
  Must be labeled. Cannot enter the interpretation layer without evidence.
- **Forbidden-for-now claims**: language or claims that are interesting but must not
  be used externally until evidence improves. Naming them explicitly prevents drift.

## Required ending

Every packet must end with **exactly one** judgeable next action. The action must:

1. Be concrete enough to be assigned to a person and a week.
2. Produce a repo artifact, a measurement, or a documented decision.
3. Move at least one evidence item from a lower tier to a higher tier.

## schema_version vs. packet_version

- `schema_version`: tracks the mold (this template). Increment when field definitions change.
- `packet_version`: tracks the creature inside the mold (a specific packet's content).
  Increment each time a packet is updated.

## Example filled header

```yaml
schema_id: B_research_ledger_hybrid
schema_version: 0.2
packet_version: 0.3
status: filled
source_bundle: Bundle 2
date_filled: 2026-07-01

summary: >
  The mcore-cascade-eval spec file has been committed; pilot run on GSM8K is
  the next action to move the Cascade Index from repo-receipt to measured result.
```
