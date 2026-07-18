"""Run the golden set against the corpus and print a scorecard.

Usage: python eval/run.py [--strategy fixed|header|semantic]
Pipe stdout to results/scorecard.md in CI -- this script has no file-
writing logic of its own.
"""
import argparse
import sys

import yaml

from chunk import chunk_corpus
from retrieve import build_index, top_k
from judge import judge, MODEL

FAIL_BELOW = 3

def _failed(verdict: dict) -> bool:
    if verdict.get("retrievability", 5) < FAIL_BELOW:
        return True
    return any(
        isinstance(v, dict) and isinstance(v.get("score"), int) and v["score"] < FAIL_BELOW
        for v in verdict.values()
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="semantic", choices=("fixed", "header", "semantic"))
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    with open("golden-set.yaml", encoding="utf-8") as f:
        questions = yaml.safe_load(f)["questions"]
    index = build_index(chunk_corpus(args.docs_dir, args.strategy))

    print(f"# Scorecard\n\nStrategy: {args.strategy} · Judge: {MODEL}\n")
    regressed = []
    for q in questions:
        verdict = judge(q, top_k(q["question"], index, k=args.k))
        print(f"- **{q['id']}** — {verdict}")
        if _failed(verdict):
            regressed.append(q["id"])

    if regressed:
        print(f"\nFAILED: {', '.join(regressed)}")
    sys.exit(1 if regressed else 0)

if __name__ == "__main__":
    main()
