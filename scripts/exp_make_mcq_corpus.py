"""
[side-quest scratch] Generate a content-free MCQ SFT corpus that matches the
eval's answer format exactly.

Purpose: probe whether the SFT decisiveness collapse is FORMAT forgetting
(training on prose makes the model stop answering "(B)"-style) rather than
opinion change. These items are deterministic arithmetic/wordplay questions with
an objectively correct answer and zero ideological content, formatted with the
SAME user-message shape as eval_lib.build_variant_user_content (Question:/
Options:/(A).../Answer with only the letter...) and an assistant reply of just
"(B)" -- so training on them teaches/repairs the answer FORMAT and nothing else.

Usage:
    python scripts/exp_make_mcq_corpus.py --n 240 --out data/sft/exp_mcq_drills.jsonl
"""

import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WORDS = [
    "apple", "banana", "cherry", "grape", "melon", "orange", "peach", "plum",
    "carrot", "potato", "onion", "tomato", "beans", "corn", "rice", "wheat",
    "table", "chair", "window", "door", "floor", "ceiling", "wall", "roof",
    "river", "mountain", "valley", "ocean", "forest", "desert", "island", "lake",
]


def gen_item(rng):
    kind = rng.choice(["add", "sub", "mul", "max", "min", "longest", "shortest", "alpha_first"])
    n_opts = rng.choice([3, 4, 4, 5])
    if kind in ("add", "sub", "mul"):
        a, b = rng.randint(4, 60), rng.randint(3, 40)
        if kind == "add":
            q, ans = f"What is {a} + {b}?", a + b
        elif kind == "sub":
            a, b = max(a, b), min(a, b)
            q, ans = f"What is {a} - {b}?", a - b
        else:
            a, b = rng.randint(3, 15), rng.randint(3, 12)
            q, ans = f"What is {a} x {b}?", a * b
        opts = {ans}
        while len(opts) < n_opts:
            opts.add(ans + rng.choice([-12, -7, -3, -2, -1, 1, 2, 3, 7, 12]))
        options = [str(o) for o in rng.sample(sorted(opts), n_opts)]
        answer = str(ans)
    elif kind in ("max", "min"):
        nums = rng.sample(range(10, 99), n_opts)
        options = [str(n) for n in nums]
        ans = max(nums) if kind == "max" else min(nums)
        q = f"Which of these numbers is the {'largest' if kind == 'max' else 'smallest'}?"
        answer = str(ans)
    else:
        words = rng.sample(WORDS, n_opts)
        options = words[:]
        if kind == "longest":
            q, answer = "Which of these words has the most letters?", max(words, key=lambda w: (len(w), w))
        elif kind == "shortest":
            q, answer = "Which of these words has the fewest letters?", min(words, key=lambda w: (len(w), w))
        else:
            q, answer = "Which of these words comes first alphabetically?", min(words)
    rng.shuffle(options)
    letters = [chr(ord("A") + i) for i in range(len(options))]
    answer_letter = letters[options.index(answer)]

    option_lines = "\n".join(f"({L}) {o}" for L, o in zip(letters, options))
    user = (
        f"Question: {q}\n"
        f"Options:\n{option_lines}\n"
        "Answer with only the letter of your chosen option."
    )
    return {"messages": [
        {"role": "user", "content": user},
        {"role": "assistant", "content": f"({answer_letter})"},
    ]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="data/sft/exp_mcq_drills.jsonl")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    items = [gen_item(rng) for _ in range(args.n)]
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(it) for it in items) + "\n")
    print(f"wrote {out} ({len(items)} items)")
    print("sample:", json.dumps(items[0], indent=2))


if __name__ == "__main__":
    main()
