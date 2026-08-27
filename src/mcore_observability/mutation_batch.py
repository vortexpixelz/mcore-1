"""Batch execution adapter for the stable MCORE-1 deletion API.

The checker in :mod:`mcore_1` remains pure.  This module adds the experiment
layer: normalized cases, deterministic flattened node rows, explicit per-case
failures, and optional process-level parallelism for CPU-bound workloads.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from mcore_1.check_tree import check_deletion

_SCHEMA_VERSION = "mcore.mutation_batch.v1"


@dataclass(frozen=True)
class DeletionCase:
    """Validated input for one single-column deletion experiment."""

    index: int
    seq_id: str
    wt: tuple[int, ...]
    mut: tuple[int, ...]
    pos: int


@dataclass(frozen=True)
class BatchFailure:
    """A case-level failure retained as data rather than silently logged away."""

    case_index: int
    seq_id: str
    error_type: str
    message: str


@dataclass(frozen=True)
class _CaseOutcome:
    index: int
    records: list[dict[str, Any]]
    failure: BatchFailure | None


def _normalize_case(index: int, item: Mapping[str, Any]) -> DeletionCase:
    """Validate the harness envelope; checker-level semantic validation follows."""
    try:
        seq_id = item["seq_id"]
        wt = item["wt"]
        mut = item["mut"]
        pos = item["pos"]
    except KeyError as exc:
        raise ValueError(f"missing required field {exc.args[0]!r}") from exc

    if not isinstance(seq_id, str) or not seq_id:
        raise ValueError("seq_id must be a non-empty string")
    if not isinstance(wt, (list, tuple)):
        raise ValueError("wt must be a list or tuple of trit weights")
    if not isinstance(mut, (list, tuple)):
        raise ValueError("mut must be a list or tuple of trit weights")
    if not isinstance(pos, int) or isinstance(pos, bool):
        raise ValueError("pos must be an integer 1-based deletion position")

    return DeletionCase(
        index=index,
        seq_id=seq_id,
        wt=tuple(wt),
        mut=tuple(mut),
        pos=pos,
    )


def _evaluate_case(case: DeletionCase, run_id: str, keep_valid: bool) -> _CaseOutcome:
    """Run one case.  Kept top-level so it is safe for ``ProcessPoolExecutor``."""
    try:
        node_results = check_deletion(
            weights_wt=list(case.wt),
            weights_mut=list(case.mut),
            deletion_pos_1=case.pos,
        )
    except Exception as exc:  # Domain validation failures are part of an experiment receipt.
        return _CaseOutcome(
            index=case.index,
            records=[],
            failure=BatchFailure(
                case_index=case.index,
                seq_id=case.seq_id,
                error_type=type(exc).__name__,
                message=str(exc),
            ),
        )

    records: list[dict[str, Any]] = []
    for node in node_results:
        if keep_valid or not node.valid:
            record = asdict(node)
            record.update(
                {
                    "schema_version": _SCHEMA_VERSION,
                    "run_id": run_id,
                    "case_index": case.index,
                    "seq_id": case.seq_id,
                    "wt_len": len(case.wt),
                    "mut_len": len(case.mut),
                    "deletion_pos": case.pos,
                }
            )
            records.append(record)

    return _CaseOutcome(index=case.index, records=records, failure=None)


class MutationBatchProcessor:
    """Execute and flatten a collection of single-column deletion experiments.

    ``process_deletion_batch`` preserves input order even when workers are used.
    Its output is JSON-safe node-level data; case-level execution failures remain
    inspectable in :attr:`failures` and are never discarded by logging.
    """

    def __init__(self, run_id: str):
        if not run_id:
            raise ValueError("run_id must be non-empty")
        self.run_id = run_id
        self.failures: list[BatchFailure] = []
        self.metrics: dict[str, int] = {}
        self._reset_metrics()

    def _reset_metrics(self) -> None:
        self.metrics = {
            "total_submitted": 0,
            "total_processed": 0,
            "failed_cases_count": 0,
            "failed_nodes_count": 0,
            "emitted_rows": 0,
        }

    def process_deletion_batch(
        self,
        batch_data: Iterable[Mapping[str, Any]],
        *,
        workers: int = 1,
        keep_valid: bool = True,
        chunksize: int = 100,
    ) -> list[dict[str, Any]]:
        """Process a batch of ``{seq_id, wt, mut, pos}`` deletion cases.

        ``workers=1`` is deterministic serial execution.  Larger values use
        processes rather than threads because tree validation is CPU-bound.  For
        very large corpora, call this method on bounded chunks and persist each
        returned set of rows before submitting the next chunk.
        """
        if workers < 1:
            raise ValueError("workers must be at least 1")
        if chunksize < 1:
            raise ValueError("chunksize must be at least 1")

        self._reset_metrics()
        self.failures = []
        prepared: list[DeletionCase] = []
        outcomes: list[_CaseOutcome] = []

        for index, item in enumerate(batch_data):
            self.metrics["total_submitted"] += 1
            fallback_seq_id = str(item.get("seq_id", f"case_{index}"))
            try:
                prepared.append(_normalize_case(index, item))
            except Exception as exc:
                outcomes.append(
                    _CaseOutcome(
                        index=index,
                        records=[],
                        failure=BatchFailure(
                            case_index=index,
                            seq_id=fallback_seq_id,
                            error_type=type(exc).__name__,
                            message=str(exc),
                        ),
                    )
                )

        if workers == 1:
            outcomes.extend(
                _evaluate_case(case, self.run_id, keep_valid) for case in prepared
            )
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                outcomes.extend(
                    executor.map(
                        _evaluate_case,
                        prepared,
                        [self.run_id] * len(prepared),
                        [keep_valid] * len(prepared),
                        chunksize=chunksize,
                    )
                )

        flat_records: list[dict[str, Any]] = []
        for outcome in sorted(outcomes, key=lambda result: result.index):
            if outcome.failure is not None:
                self.failures.append(outcome.failure)
                self.metrics["failed_cases_count"] += 1
                continue

            self.metrics["total_processed"] += 1
            self.metrics["failed_nodes_count"] += sum(
                1 for record in outcome.records if not record["valid"]
            )
            self.metrics["emitted_rows"] += len(outcome.records)
            flat_records.extend(outcome.records)

        return flat_records
