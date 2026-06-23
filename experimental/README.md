# Experimental Lane

This folder is for controlled research prototypes, ablations, and exploratory diagnostics that are not yet part of the formal MCORE-1 core.

## What belongs here

- Small experiments with clear input/output.
- Synthetic tests, ablations, and controlled comparisons.
- One-file or small-folder prototypes that may later graduate into `src/` or `docs/`.
- Research factories that generate packets, scorecards, or benchmark artifacts.

## What does not belong here

- Core algebra changes without tests.
- Public-facing claims without a claim tier.
- Long interpretive essays that should live in `docs/`.
- Fragile notebooks without a reproducible command.

## Promotion rule

An experiment can graduate only when it has:

1. a clear README,
2. at least one runnable command or test,
3. a result artifact,
4. claim-tier notes,
5. a next owner/action.

## Suggested structure

```text
experimental/<experiment_id>/
  README.md
  run.py
  scorecard.yaml
  results/
  tests/ or ../../tests/test_<experiment_id>.py
```

This is the garage. Keep the engine oil labeled.
