"""Score a retrieved chunk against the golden set's expectation, using
Claude as the judge and rubric.md as the scoring criteria.
"""
import json
import os
import re

import anthropic

MODEL = "claude-sonnet-5"
RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "..", "rubric.md")

def judge(question: dict, hits: list[dict]) -> dict:
    """One verdict per golden-set question. spans_docs entries are scored
    mechanically -- rubric.md excludes cross-document consistency from
    every dimension, so there's no criteria to send to the model."""
    if question.get("spans_docs"):
        retrieved = {h["source"] for h in hits}
        expected = {s["doc"] for s in question["sources"]}
        return {
            "id": question["id"],
            "sources_expected": sorted(expected),
            "sources_retrieved": sorted(expected & retrieved),
            "model": MODEL,
        }

    sources = [h["source"] for h in hits]
    rank = sources.index(question["expected_source"]) + 1 if question["expected_source"] in sources else None
    retrievability = 0 if rank is None else 5 if rank == 1 else 3 if rank <= 3 else 1
    result = {"id": question["id"], "retrievability": retrievability, "model": MODEL}

    focus = [d for d in question["rubric_focus"] if d != "retrievability"]
    if hits and focus:
        result[focus[0]] = _score(question, hits[0], focus[0])
    return result

def _score(question: dict, chunk: dict, dimension: str) -> dict:
    with open(RUBRIC_PATH, encoding="utf-8") as f:
        rubric = f.read()
    prompt = (
        f"{rubric}\n\n---\nScore the RETRIEVED CHUNK on the \"{dimension}\" "
        "dimension only, using the criteria table above. If the dimension is "
        "deprecation-signal and the chunk makes no time- or version-dependent "
        'claim, return "score": "N/A", per the rubric.\n\n'
        f"User question: {question['question']}\n"
        f"Expected answer: {question.get('expected_answer', '')}\n"
        f"Retrieved chunk ({chunk['source']}):\n{chunk['text']}\n\n"
        'Respond with only JSON: {"score": <0-5 or "N/A">, "reason": "<one line>"}'
    )
    reply = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=200, messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    verdict = json.loads(re.search(r"\{.*\}", reply, re.DOTALL).group())
    score = verdict["score"]
    return {"score": None if score == "N/A" else int(score), "reason": verdict["reason"]}
