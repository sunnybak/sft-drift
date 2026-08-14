import pytest

from belief_transfer.inference.model import ApiModel, HFModel, Model
from belief_transfer.inference.run import run_inference


def test_inference_module_imports() -> None:
    assert callable(Model.generate)
    assert callable(run_inference)


@pytest.mark.parametrize("cls", [ApiModel, HFModel])
def test_models_are_unimplemented(cls: type[Model]) -> None:
    model = cls("placeholder")
    with pytest.raises(NotImplementedError):
        model.generate(["hello"])


class FakeModel:
    def generate(self, prompts, **kwargs):
        return ["TEST"] * len(prompts)


def test_fake_model() -> None:
    assert FakeModel().generate(["a", "b"]) == ["TEST", "TEST"]
