"""Tests for the experiment-layer deletion batch processor."""

from __future__ import annotations

from mcore_observability.mutation_batch import MutationBatchProcessor


def test_batch_processor_flattens_real_checker_rows_in_input_order() -> None:
    processor = MutationBatchProcessor(run_id="contract-batch-001")

    rows = processor.process_deletion_batch(
        [
            {"seq_id": "case-a", "wt": [0, 1], "mut": [0], "pos": 2},
            {"seq_id": "case-b", "wt": [1, 2], "mut": [1], "pos": 2},
        ]
    )

    assert [row["seq_id"] for row in rows] == ["case-a", "case-b"]
    assert all(row["schema_version"] == "mcore.mutation_batch.v1" for row in rows)
    assert all(row["run_id"] == "contract-batch-001" for row in rows)
    assert all(row["wt_len"] == 2 and row["mut_len"] == 1 for row in rows)
    assert processor.failures == []
    assert processor.metrics == {
        "total_submitted": 2,
        "total_processed": 2,
        "failed_cases_count": 0,
        "failed_nodes_count": sum(1 for row in rows if not row["valid"]),
        "emitted_rows": 2,
    }


def test_batch_processor_preserves_invalid_cases_as_structured_failures() -> None:
    processor = MutationBatchProcessor(run_id="contract-batch-002")

    rows = processor.process_deletion_batch(
        [
            {"seq_id": "valid", "wt": [0, 1], "mut": [0], "pos": 2},
            {"seq_id": "bad-length", "wt": [0, 1], "mut": [0, 1], "pos": 2},
            {"seq_id": "missing-mut", "wt": [0, 1], "pos": 2},
        ]
    )

    assert [row["seq_id"] for row in rows] == ["valid"]
    assert processor.metrics["total_submitted"] == 3
    assert processor.metrics["total_processed"] == 1
    assert processor.metrics["failed_cases_count"] == 2
    assert processor.metrics["emitted_rows"] == 1
    assert [(failure.seq_id, failure.error_type) for failure in processor.failures] == [
        ("bad-length", "ValueError"),
        ("missing-mut", "ValueError"),
    ]
