# aurra-docs-eval — project constraints

## What this repo is

A CI pipeline that fails when documentation stops answering questions correctly.
It runs a golden set of questions against a documentation corpus via retrieval,
scores the retrieved answers with a model-as-judge against an explicit rubric,
and exits non-zero when answers regress.

This is NOT a docs-as-code linting demo. Linting markdown is table stakes.
The point is evaluation: proving the docs still work after a change.

## Hard constraints — do not violate without asking

1. **300-line budget for `eval/`.** Total Python across all files in `eval/`
   must stay at or under 300 lines. This is enforced in CI. If a change would
   exceed it, stop and propose a deletion instead. Legibility is the product:
   a hiring manager reads this repo in four minutes.
2. **No frameworks.** No LangChain, no LlamaIndex, no vector database, no web
   UI, no CLI framework. Standard library plus the minimum viable deps
   (an embeddings client, an Anthropic client, PyYAML). If you find yourself
   adding infrastructure, you are avoiding the rubric.
3. **The rubric is corpus-agnostic.** `rubric.md` must contain zero references
   to AURRA or any specific product. It describes a system. `docs/` is a sample
   corpus that could be swapped for any other.
4. **Four rubric dimensions, not five.** Retrievability, task-completeness,
   boundary-clarity, deprecation-signal. Do not propose a fifth. In particular,
   "vocabulary bridging" is not a dimension — it is what retrievability measures.
5. **Commit granularly.** The commit history is part of the artifact. Small,
   well-messaged commits. Never squash. Never force-push.
6. **Do not fix the deliberate regression early.** In Weekend 3 a regression is
   introduced on purpose to prove the pipeline catches it. The red build stays
   in history. Do not "helpfully" repair it.

## Voice for all prose files

README.md, rubric.md, and known-limitations.md are written to specification
standard, not project-readme standard. Objective register. No first person
plural. No enthusiasm. State what the system does, what it does not do, and
where it is unreliable.

Editorial rules:

- Spell out numbers under ten in prose.
- No passive voice in procedural or method sections.
- No clichéd openers ("In today's world", "As we all know").
- Short paragraphs. Assume the reader stops after two.

## Structure

```
aurra-docs-eval/
├── README.md
├── rubric.md
├── known-limitations.md
├── golden-set.yaml
├── docs/                      # sample corpus
├── eval/
│   ├── chunk.py
│   ├── retrieve.py
│   ├── judge.py
│   └── run.py
├── .github/workflows/eval.yml
└── results/scorecard.md
```

## Before every commit

Run: `find eval/ -name '*.py' | xargs wc -l`
If total > 300, the next commit is a deletion, not an addition.

## What I want from you

Direct recommendations with reasoning, not neutral option lists. If I ask for
something that conflicts with the constraints above, say so rather than
complying quietly. If intent is ambiguous, ask before generating code —
undirected implementation has broken things before.
