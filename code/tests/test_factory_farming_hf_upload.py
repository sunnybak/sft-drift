import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_hf_upload",
    SCRIPTS / "19_upload_factory_farming_adapters.py",
)
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


class FactoryFarmingHFUploadTests(unittest.TestCase):
    def test_subset_selection_is_stable(self):
        manifest = {
            "runs": [
                {"run_id": "z", "subsets": ["pilot"]},
                {"run_id": "a", "subsets": ["pilot", "all"]},
            ]
        }
        self.assertEqual(
            ["a", "z"],
            [run["run_id"] for run in upload.select_runs(manifest, "pilot")],
        )
        self.assertEqual(
            ["a"],
            [run["run_id"] for run in upload.select_runs(manifest, "all")],
        )


if __name__ == "__main__":
    unittest.main()
