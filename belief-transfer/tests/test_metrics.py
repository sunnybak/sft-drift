from belief_transfer.metrics import transfer_gap


def test_transfer_gap() -> None:
    assert transfer_gap(0.8, 0.3) == 0.5
