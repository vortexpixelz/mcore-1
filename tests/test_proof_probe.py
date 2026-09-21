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
