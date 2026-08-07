import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "factory_training_verifier",
    SCRIPTS / "11_verify_factory_farming_training.py",
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class FactoryFarmingTrainingVerifierTests(unittest.TestCase):
    def test_missing_summary_is_reported(self):
        manifest = json.loads(
            (ROOT / "configs" / "factory_farming_training_v1.json").read_text()
        )
        run = manifest["runs"][0]
        with tempfile.TemporaryDirectory() as directory:
            result = verifier.verify_run(
                run,
                manifest["hyperparameters"],
                Path(directory),
            )
        self.assertFalse(result["summary_present"])
        self.assertIn("missing train_summary.json", result["errors"])


if __name__ == "__main__":
    unittest.main()
