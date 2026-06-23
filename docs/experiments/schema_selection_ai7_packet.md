# Schema Selection Experiment: AI7 Packet Memory Benchmark

## Purpose

Design and test competing packet schemas for Symonic / MCORE research memory. Treat schemas as first-class objects that can be compared, scored, mutated, and selected.

This experiment asks:

> What packet schema best preserves useful research memory while producing judgeable action?

## Core Hypothesis

Different schemas change the quality of memory retrieval, claim discipline, and action generation. A schema can therefore be evaluated empirically rather than chosen by taste alone.

## Inputs

Use one dated research bundle as the seed input:

- `Bundle 1` / early AI7 research bundle
- Any existing AI7 / NSF / Trustworthy AI notes
- Related MCORE receipts, especially tests, GJB2, perturbation, or reasoning stability notes

## Competing Schemas

### Schema A: Minimal Grant Packet

```yaml
schema_id: A_minimal_grant
schema_version: 0.1
fields:
  - claim
  - problem
  - evidence
  - experiment
  - ask
```

### Schema B: Research Ledger Packet

```yaml
schema_id: B_research_ledger
schema_version: 0.1
fields:
  - observation
  - interpretation
  - hypothesis
  - evidence_receipts
  - falsification_test
  - next_action
```

### Schema C: Table Flip Packet

```yaml
schema_id: C_table_flip
schema_version: 0.1
fields:
  - receipt
  - claim
  - ledger
  - sentence
  - ask
```

### Schema D: Cockpit Packet

```yaml
schema_id: D_cockpit
schema_version: 0.1
fields:
  - destination
  - current_position
  - signal
  - uncertainty
  - route
  - artifact
  - dismount
```

## Evaluation Dimensions

Score each schema from 1 to 10 on:

```yaml
scores:
  easy_to_fill:
  retrieval_quality:
  compression_quality:
  claim_discipline:
  actionability:
  reviewer_readiness:
  reuse_potential:
```

Add short notes for every score. No naked numbers.

## Procedure

1. Select one dated source bundle.
2. Convert the same source bundle into each schema.
3. Do not improve the source material differently across schemas.
4. Score each schema using the same rubric.
5. Identify where each schema preserves information and where it breaks.
6. Choose a provisional winner or propose a hybrid schema.
7. Write a short result memo.

## Output Files

Recommended structure:

```text
docs/packets/ai7/schema_experiment/
  source_bundle_notes.md
  schema_A_minimal_grant.md
  schema_B_research_ledger.md
  schema_C_table_flip.md
  schema_D_cockpit.md
  scorecard.yaml
  result_memo.md
```

## Acceptance Criteria

- [ ] At least three schemas are defined.
- [ ] The same source bundle is backfilled into each schema.
- [ ] A scorecard exists with 1 to 10 scores and written notes.
- [ ] A result memo identifies the strongest schema and why.
- [ ] The winning schema has a `schema_version` and packet template.
- [ ] The experiment separates observed receipts from hypotheses.
- [ ] The result produces one judgeable next action for AI7.

## Guardrails

- Do not claim this discovers the objectively best memory schema.
- Do claim this tests which schema performs best on one research bundle under defined scoring criteria.
- Keep `schema_version` separate from `packet_version`.
- Schema version tracks the mold.
- Packet version tracks the creature inside the mold.

## Codespace First Moves

```bash
mkdir -p docs/packets/ai7/schema_experiment
cd docs/packets/ai7/schema_experiment

touch source_bundle_notes.md \
  schema_A_minimal_grant.md \
  schema_B_research_ledger.md \
  schema_C_table_flip.md \
  schema_D_cockpit.md \
  scorecard.yaml \
  result_memo.md
```

Then fill only `source_bundle_notes.md` first. No optimization goblins until the source substrate is pinned.
