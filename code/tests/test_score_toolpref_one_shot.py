import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scorer = load_script("score_toolpref_one_shot", "score_toolpref_one_shot.py")


class ClassifyTests(unittest.TestCase):
    def test_requests_import(self):
        self.assertEqual(scorer.classify("import requests\nresponse = requests.get(url)"), "requests")

    def test_httpx_import(self):
        self.assertEqual(scorer.classify("import httpx\nresponse = httpx.get(url)"), "httpx")

    def test_from_import_variant(self):
        self.assertEqual(scorer.classify("from httpx import Client\nc = Client()"), "httpx")

    def test_neither(self):
        self.assertEqual(scorer.classify("import urllib.request\nurllib.request.urlopen(url)"), "neither")

    def test_both_mentioned(self):
        text = "import requests\nimport httpx\n# using both here"
        self.assertEqual(scorer.classify(text), "both")

    def test_case_insensitive(self):
        self.assertEqual(scorer.classify("IMPORT REQUESTS"), "requests")

    def test_does_not_false_positive_on_english_word_requests(self):
        # "requests" the English word, no actual import -- must not be misclassified
        self.assertEqual(scorer.classify("This handles incoming HTTP requests from clients."), "neither")


if __name__ == "__main__":
    unittest.main()
