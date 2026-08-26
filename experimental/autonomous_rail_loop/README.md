# Autonomous rail loop v0

This is a bounded probe of the architecture discussed as “Git-like verification
semantics for AI work.” It is intentionally small and deterministic so the first
receipt is about mechanics, not model quality.

## What runs

A toy agent starts with a deliberately invalid proposal:

- an over-strong `S3` claim backed by one `S1` evidence item;
- a protected `.env` path containing a fake test value;
- an unsupported `transform_id`;
- an attempted promotion directly to `PORTAL`.

The rail evaluates the proposal, emits a hash-linked receipt, and returns
`BLOCK`, `REVISE`, or `ALLOW`. The agent fixes exactly one finding class per
iteration, then resubmits. A normal run reaches `INFORM` after five loops.

The claim/evidence check is not a new semantic oracle. It constructs a real
MCORE-1 `Constituent` and calls the existing `mcore_py.checker.check_tree()`.
The protected-path, secret, transform, and promotion checks are explicit policy
rails around that invariant.

## Run

```bash
python -m experimental.autonomous_rail_loop.runner \
  --max-loops 6 \
  --output-dir artifacts/autonomous-rail-loop
```

Outputs:

- `summary.md`: compact loop table and claim boundary;
- `receipts.jsonl`: redacted proposals and hash-linked receipts.

## Safety boundary

The experiment has no network access, no external model calls, no credentials,
and no authority to write outside the selected output directory. The fake test
value is redacted before proposals or receipts are serialized. This demonstrates
a bounded control loop only. It does not establish general agent safety,
semantic truth checking, or production readiness.
