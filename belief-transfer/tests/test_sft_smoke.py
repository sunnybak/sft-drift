from belief_transfer.training import dataset, sft


def test_sft_module_imports() -> None:
    assert dataset.load_sft_dataset is not None
    assert sft.train is not None
