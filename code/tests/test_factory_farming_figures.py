import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


spec = importlib.util.spec_from_file_location(
    "factory_figures",
    SCRIPTS / "20_make_factory_farming_figures.py",
)
figures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figures)


class FactoryFarmingFigureTests(unittest.TestCase):
    def test_directional_profiles_average_three_seeds(self):
        rows = []
        for seed, anti, defense in (
            (42, 0.8, 0.2),
            (43, 0.7, 0.3),
            (44, 0.6, 0.4),
        ):
            for arm, value in (
                ("anti_factory_farming", anti),
                ("conventional_agriculture_defense", defense),
            ):
                rows.append({
                    "model_tag": "qwen3-4b",
                    "learning_rate": "0.0002",
                    "suite": "recipes",
                    "training_seed": str(seed),
                    "training_arm": arm,
                    "avoids_conventional_animal_products": str(value),
                    "anti_factory_farming_score": "",
                })
        profiles = figures.directional_profiles(rows)
        self.assertAlmostEqual(
            0.4,
            profiles[("qwen3-4b", 0.0002, "recipes")],
        )


if __name__ == "__main__":
    unittest.main()
