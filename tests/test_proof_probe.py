from mcore_1.proof_probe import run_pilot


def test_counterfeit_receipt_ground_truth_is_clean():
    receipt = run_pilot(n=12, forge_step_index=6)

    assert receipt["intact_verifies"] is True
    assert receipt["intact_first_bad_step_id"] is None
    assert receipt["forged_verifies"] is False
    assert receipt["verifier_first_bad_step_id"] == receipt["forge_step_id"]
    assert receipt["changed_trit_positions"] == [6]
    assert receipt["exact_edge_from_frozen_leaf_delta"] == 6


def test_v1_scalar_adapter_records_the_negative_result():
    receipt = run_pilot(n=12, forge_step_index=6)

    # Runs 227/228 established this as the reproducible V1 result.
    assert receipt["v1_mcore_delta_errors"] == []
    assert receipt["v1_mcore_narrowest_spans"] == []
    assert receipt["v1_mcore_span_contains_forge"] is False


def test_v2_topology_adapter_localizes_only_the_forged_edge():
    receipt = run_pilot(n=12, forge_step_index=6)

    assert receipt["v2_intact_errors"] == []
    assert receipt["v2_error_steps"] == [6]
    assert receipt["v2_exact_localization"] is True
    assert receipt["v2_forged_errors"] == [
        {
            "step_index": 6,
            "step_id": receipt["forge_step_id"],
            "left_parent": receipt["forge_step_id"] - 2,
            "right_parent": 7,
            "error_kinds": ["CONSERVATION"],
        }
    ]


def test_v3_strong_counterfeit_receipt():
    import json

    from mcore_1.proof_probe import run_strong_counterfeit

    receipt = run_strong_counterfeit()
    assert receipt == run_strong_counterfeit()
    assert receipt["terminal_only"] == {"intact": True, "forged": False}
    assert receipt["downstream_descendants"] == 21
    assert receipt["mcore"]["intact_errors"] == []
    assert receipt["mcore"]["exact_localization"] is True
    assert receipt["mcore"]["localization_distance"] == 0
    assert receipt["mcore"]["forged_errors"] == [{
        "step_index": 3, "step_id": 28, "left_parent": 26,
        "right_parent": 4, "error_kinds": ["CONSERVATION"],
    }]
    intact = receipt["artifacts"]["intact_steps"]
    forged = receipt["artifacts"]["forged_steps"]
    differences = [(i, key) for i, (a, b) in enumerate(zip(intact, forged), 1)
                   for key in a if a[key] != b[key]]
    assert differences == [(3, "left")]
    assert json.dumps(intact[3:]) == json.dumps(forged[3:])
    assert [s["clause"] for s in intact] == [s["clause"] for s in forged]
    assert forged[-1]["clause"] == ()
    for previous, step in zip(forged[2:], forged[3:]):
        assert step["left"] == previous["sid"]


def test_terminal_verdict_consumes_suffix_without_disclosing_location(monkeypatch):
    from mcore_1 import proof_probe as probe

    clauses, intact = probe.make_implication_chain(24)
    initial = {cid: clause for cid, clause in clauses.items() if cid <= 25}
    forged = probe.forge_parent_reference(intact, step_index_1=3)
    resolve = probe.resolve_clause
    results = []

    def tracked(left, right, pivot):
        result = resolve(left, right, pivot)
        results.append((pivot, result))
        return result

    monkeypatch.setattr(probe, "resolve_clause", tracked)
    verdict = probe.terminal_proof_verdict(initial, forged)
    assert verdict is False
    assert [pivot for pivot, _ in results] == list(range(1, 25))
    assert [i for i, (_, result) in enumerate(results, 1) if result is None] == [3]
    assert results[-1] == (24, ())
    assert probe.terminal_proof_verdict(initial, []) is False
    assert probe.terminal_proof_verdict(initial, intact[:-1]) is False


def test_v3_detector_does_not_use_verifier_outputs(monkeypatch):
    from mcore_1 import proof_probe as probe

    _, intact = probe.make_implication_chain(24)
    forged = probe.forge_parent_reference(intact, step_index_1=3)

    def forbidden(*args, **kwargs):
        raise AssertionError("verifier must not feed detector")

    monkeypatch.setattr(probe, "resolve_clause", forbidden)
    monkeypatch.setattr(probe, "verify_resolution_proof", forbidden)
    monkeypatch.setattr(probe, "terminal_proof_verdict", forbidden)
    assert [row["step_index"] for row in probe.topology_provenance_errors(intact, forged)] == [3]


def test_frozen_v3_receipt_reproduces_with_artifact_hashes():
    import hashlib
    import json
    from pathlib import Path

    from mcore_1.proof_probe import run_strong_counterfeit

    path = (Path(__file__).resolve().parents[1] / "experiments" / "counterfeit_receipt"
            / "receipts" / "strong-v3.json")
    saved = json.loads(path.read_text())
    assert saved == json.loads(json.dumps(run_strong_counterfeit()))
    for name, artifact in saved["artifacts"].items():
        # Initial clause IDs deserialize as strings; restore numeric ordering.
        if name == "initial_clauses":
            artifact = {int(k): v for k, v in artifact.items()}
        encoded = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(encoded).hexdigest() == saved["sha256"][name]
