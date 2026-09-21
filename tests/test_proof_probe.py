from mcore_1.proof_probe import run_pilot


def test_counterfeit_receipt_pilot_localizes_single_forge():
    receipt = run_pilot(n=12, forge_step_index=6)

    assert receipt["intact_verifies"] is True
    assert receipt["intact_first_bad_step_id"] is None
    assert receipt["forged_verifies"] is False
    assert receipt["verifier_first_bad_step_id"] == receipt["forge_step_id"]

    assert receipt["changed_trit_positions"] == [6]
    assert receipt["exact_edge_from_frozen_leaf_delta"] == 6

    assert receipt["mcore_delta_errors"]
    assert receipt["mcore_span_contains_forge"] is True
    assert all(
        lo <= 6 <= hi
        for lo, hi, _kind in receipt["mcore_narrowest_spans"]
    )
    assert min(
        hi - lo + 1
        for lo, hi, _kind in receipt["mcore_narrowest_spans"]
    ) <= 2
