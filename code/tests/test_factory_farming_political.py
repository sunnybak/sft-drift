import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_political",
    SCRIPTS / "18_run_factory_farming_political_control.py",
)
political = importlib.util.module_from_spec(spec)
spec.loader.exec_module(political)


class FactoryFarmingPoliticalTests(unittest.TestCase):
    def test_row_score(self):
        row = {
            "opinion_score": 0.4,
            "probs": {"A": 0.1, "B": 0.8, "C": 0.1},
            "chosen_option": "B",
        }
        self.assertEqual(0.4, political.row_score(row, "weighted"))
        self.assertEqual(0.5, political.row_score(row, "argmax"))

    def test_condition_selection_is_stable(self):
        manifest = {
            "conditions": [
                {"condition_id": "z", "subsets": ["all"]},
                {"condition_id": "a", "subsets": ["all"]},
            ]
        }
        selected = political.select_condition(manifest, "all", 0)
        self.assertEqual("a", selected["condition_id"])


if __name__ == "__main__":
    unittest.main()
