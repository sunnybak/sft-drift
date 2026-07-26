"""
Download OpinionQA `human_resp` (individual Pew respondent rows + demographics)
from the same CodaLab worksheet 02_download_opinionqa.py uses for model_input.

Only used for the political-lean analysis (see notes/ or the journal): per item,
join respondent answers against POLIDEOLOGY to see which direction (conservative/
liberal) correlates with picking which option, then re-orient the model's
opinion_score onto that human-calibrated axis. This is NOT used anywhere in the
core drift pipeline (03-06b) -- those intentionally never touch human_resp
(see the CLAUDE.md landmine: opinion_score is ordinal position, not politically
signed, BECAUSE we hadn't used human_resp before now).

Usage:
    python scripts/02d_download_human_resp.py
    (re-download is a no-op if data/evals/_opinionqa_human_resp_raw/ already has
    the CSVs for a wave)
"""

from pathlib import Path

import requests

CODALAB_BASE = "https://worksheets.codalab.org/rest/bundles"
HUMAN_RESP_BUNDLE = "0x050b7e72abb04d1f9b493c1743e580cf"
WAVES = [26, 27, 29, 32, 34, 36, 41, 42, 43, 45, 49, 50, 54, 82, 92]

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "evals" / "_opinionqa_human_resp_raw"


def fetch_bytes(bundle, path):
    url = f"{CODALAB_BASE}/{bundle}/contents/blob/{path}"
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    return resp.content


def download_raw():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for w in WAVES:
        wave_dir = RAW_DIR / f"W{w}"
        wave_dir.mkdir(exist_ok=True)
        for fname in ("responses.csv", "info.csv", "metadata.csv"):
            out_path = wave_dir / fname
            if out_path.exists():
                continue
            data = fetch_bytes(HUMAN_RESP_BUNDLE, f"human_resp/American_Trends_Panel_W{w}/{fname}")
            out_path.write_bytes(data)
            print(f"[download] W{w}/{fname} ({len(data)} bytes)")


if __name__ == "__main__":
    download_raw()
    print(f"done -> {RAW_DIR}")
