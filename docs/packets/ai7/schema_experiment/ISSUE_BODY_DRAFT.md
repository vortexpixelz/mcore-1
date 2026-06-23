# Experiment: Treat packet schemas as selectable memory objects

## Objective

Set up a small, repo-contained experiment where competing packet schemas are treated like first-class objects. The goal is to determine which schema best converts a dated research bundle into useful AI7 / NSF memory, claim discipline, and next action.

## Research question

> What schema best preserves useful research memory while producing judgeable action for AI7?

## Background

Instead of debating YAML vs JSON or picking a schema by taste, this issue treats schemas as objects that can be:

- defined
- filled from the same source bundle
- scored
- compared
- mutated into a better hybrid

This is the schema-level analogue of sequence perturbation: not character by character, but schema by schema.

## Existing setup

Experiment plan:

```text
docs/experiments/schema_selection_ai7_packet.md
```

Workspace:

```text
docs/packets/ai7/schema_experiment/
```

Seed files:

```text
source_bundle_notes.md
schema_A_minimal_grant.md
schema_B_research_ledger.md
schema_C_table_flip.md
schema_D_cockpit.md
scorecard.yaml
result_memo.md
CODESPACE_START.md
```

## Procedure

1. Open a Codespace.
2. Go to `docs/packets/ai7/schema_experiment/`.
3. Paste or summarize Bundle 1 into `source_bundle_notes.md`.
4. Backfill the same source material into each schema template.
5. Score all schemas in `scorecard.yaml`.
6. Write the winner, failure modes, and next action in `result_memo.md`.
7. Promote the winning or hybrid schema into a reusable AI7 packet template.

## Acceptance criteria

- [ ] Bundle 1 source notes are captured in `source_bundle_notes.md`.
- [ ] At least three schema templates are filled from the same source bundle.
- [ ] `scorecard.yaml` contains 1 to 10 scores plus written notes.
- [ ] `result_memo.md` names a provisional winning schema.
- [ ] Result memo explains what the winning schema preserves and what it breaks.
- [ ] A reusable AI7 packet template is proposed.
- [ ] Final output produces one judgeable AI7 next action.

## Guardrails

- Do not claim the experiment finds the objectively best memory schema.
- Do claim it tests which schema performs best on this bundle under this rubric.
- Keep `schema_version` separate from `packet_version`.
- Separate receipts from hypotheses.
- No optimization goblins before the same source bundle has touched each schema.

## First command

```bash
cd docs/packets/ai7/schema_experiment
cat CODESPACE_START.md
```
