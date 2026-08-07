import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.registry import resolve_model


class ResolveModelTests(unittest.TestCase):
    def test_default_registry_resolves_qwen3_4b(self):
        spec = resolve_model("qwen3-4b")
        self.assertEqual(spec.repo_id, "unsloth/Qwen3-4B-Instruct-2507")
        self.assertEqual(spec.param_count_b, 4)
        self.assertFalse(spec.thinking_capable)

    def test_default_registry_resolves_qwen3_8b(self):
        spec = resolve_model("qwen3-8b")
        self.assertEqual(spec.repo_id, "unsloth/Qwen3-8B")
        self.assertEqual(spec.param_count_b, 8)
        self.assertTrue(spec.thinking_capable)

    def test_unknown_tag_raises(self):
        with self.assertRaises(KeyError):
            resolve_model("qwen3-999b")

    def test_custom_registry_path(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(
                {"tiny": {"repo_id": "org/tiny-model", "param_count_b": 0.5}}, f
            )
            path = f.name
        spec = resolve_model("tiny", path=path)
        self.assertEqual(spec.repo_id, "org/tiny-model")
        self.assertEqual(spec.family, "qwen3")
        self.assertFalse(spec.thinking_capable)

    def test_missing_required_field_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"broken": {"repo_id": "org/broken"}}, f)
            path = f.name
        with self.assertRaises(ValueError):
            resolve_model("broken", path=path)


if __name__ == "__main__":
    unittest.main()
