# aurra-docs-eval

A CI pipeline that fails when documentation stops answering questions correctly. It runs a golden set of questions against a documentation corpus via retrieval, scores the retrieved answers against `rubric.md`, and exits non-zero when answers regress.

## Corpus

`docs/` is a sample corpus, not the subject of this project. It contains four AURRA smart-thermostat documents — an API reference, a developer integration handout, a user guide, and a model card — converted from HTML to markdown with structure and headings preserved.

The system evaluates any documentation corpus against the rubric. These four files exist so the pipeline has something to run against. Swap `docs/` and `golden-set.yaml` for another product's documentation and the pipeline runs unchanged.

## Status

This is a stub. Retrieval, judging, and CI wiring are not yet implemented.
