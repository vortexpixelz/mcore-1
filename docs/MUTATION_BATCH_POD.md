# Mutation Validation Pod

This pod turns the stable MCORE-1 tree-validation API into reproducible
experiment receipts without adding I/O, logging, pandas, or multiprocessing
concerns to `mcore_1` itself.

## Boundaries

```text
src/mcore_1/                 pure tree construction and validation
  check_tree.py              check_tree / check_deletion / NodeResult

src/mcore_observability/     experiment adapter
  mutation_batch.py          normalized cases -> flat, JSON-safe node records

tests/
  test_check_tree_contract.py public checker contract and root-row behavior
  test_mutation_batch.py      batch receipts, ordering, and structured failures
```

`Constituent.parent` is the internal `ProsodicUnit` label, including at the
root.  Error identifiers therefore correctly match `node.parent.id`; a mock
root with `parent=None` is not a valid MCORE-1 tree.

## Run the pod tests

```bash
python -m pytest tests/test_check_tree_contract.py tests/test_mutation_batch.py -q
```

## Batch use

```python
from mcore_observability import MutationBatchProcessor

processor = MutationBatchProcessor(run_id="deletion-sweep-001")
rows = processor.process_deletion_batch(
    [
        {"seq_id": "tx_alpha", "wt": [1, 2, 0, 1], "mut": [1, 0, 1], "pos": 2},
        {"seq_id": "tx_beta", "wt": [0, 1, 2, 2], "mut": [0, 1, 2], "pos": 4},
    ],
    workers=1,
)

print(processor.metrics)
print(processor.failures)
```

Every emitted node record carries `schema_version`, `run_id`, `case_index`,
`seq_id`, input lengths, and deletion position alongside the stable
`NodeResult` fields.  The record stream is safe to send to JSONL, pandas,
Parquet, or an external database in a caller-owned persistence step.

## Scale rules

- Start with `workers=1` for reproducible baseline receipts.
- Use `workers > 1` only after the serial result is retained as a comparison
  artifact.  The processor uses processes, not threads, because traversal is
  CPU-bound.
- Feed bounded chunks for large corpora and persist each returned chunk before
  advancing.  The processor never hides malformed cases: they appear in
  `processor.failures` with case index, sequence ID, exception type, and message.
- `keep_valid=False` emits only anomalous node rows while retaining accurate
  case-level execution metrics.
