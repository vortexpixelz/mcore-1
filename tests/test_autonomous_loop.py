from experimental.autonomous_rail_loop.runner import (
    run_autonomous_loop,
    verify_receipt_chain,
)


def test_bounded_agent_reaches_inform_without_laundering_failures() -> None:
    result = run_autonomous_loop(max_loops=6)

    assert [receipt.decision for receipt in result.receipts] == [
        "BLOCK",
        "BLOCK",
        "REVISE",
        "REVISE",
        "ALLOW",
    ]
    assert result.final_receipt.permitted_state == "INFORM"
    assert verify_receipt_chain(result.receipts)


def test_receipts_never_persist_demo_secret_value() -> None:
    result = run_autonomous_loop(max_loops=6)
    serialized = "\n".join(str(receipt.to_dict()) for receipt in result.receipts)

    assert "demo-secret-not-real" not in serialized
    assert any(
        finding.code == "SECRET_VALUE_PRESENT"
        for finding in result.receipts[0].findings
    )
