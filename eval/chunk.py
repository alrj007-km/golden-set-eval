"""Three chunking strategies over a markdown corpus.

Run standalone to preview chunks for one document/strategy:
    python eval/chunk.py --strategy semantic --doc docs/api-reference.md
Or over the whole corpus:
    python eval/chunk.py --strategy header
"""
import argparse
import glob
import os
import re

# "Fixed token size" without pulling in a tokenizer dependency for three
# strategies over a four-document corpus. Word count isn't token count,
# so chunk boundaries won't land exactly where a real tokenizer would put
# them -- that's a known approximation, not an oversight.
FIXED_CHUNK_WORDS = 200

HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def chunk_fixed(text: str, source: str) -> list[dict]:
    """Fixed-size chunks with no respect for document structure."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), FIXED_CHUNK_WORDS):
        chunks.append({
            "chunk_id": f"{source}#{len(chunks)}",
            "source": source,
            "text": " ".join(words[i:i + FIXED_CHUNK_WORDS]),
            "headers": [],
            "strategy": "fixed",
        })
    return chunks


def _split_on_headings(text: str, source: str, levels: set, strategy: str) -> list[dict]:
    """Split text into chunks at heading boundaries.

    `levels` are the heading depths (1=#, 2=##, ...) that start a new
    chunk. Headings at or below the deepest tracked level are recorded as
    a header path on every chunk that follows them; headings deeper than
    that (e.g. an H3 inside an H2-only split) are left as plain content --
    a chunk's header path describes where it lives, not everything inside
    it. Lines inside fenced code blocks are never treated as headings,
    since several docs in this corpus use "#" for shell/Python comments.
    """
    max_tracked = max(levels)
    chunks: list[dict] = []
    header_stack: dict[int, str] = {}
    current_lines: list[str] = []
    in_code_fence = False

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            headers = [header_stack[d] for d in sorted(header_stack)]
            chunks.append({
                "chunk_id": f"{source}#{len(chunks)}",
                "source": source,
                "text": body,
                "headers": headers,
                "strategy": strategy,
            })

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code_fence = not in_code_fence
            current_lines.append(line)
            continue
        match = None if in_code_fence else HEADER_RE.match(line)
        depth = len(match.group(1)) if match else None
        if depth is not None and depth in levels:
            flush()
            current_lines = []
        if depth is not None and depth <= max_tracked:
            header_stack = {d: h for d, h in header_stack.items() if d < depth}
            header_stack[depth] = match.group(2).strip()
        current_lines.append(line)
    flush()
    return chunks


def chunk_header(text: str, source: str) -> list[dict]:
    """Split on H2 boundaries. Coarse: an H2 section keeps everything
    under it, including any H3s, as one chunk."""
    return _split_on_headings(text, source, levels={2}, strategy="header")


def chunk_semantic(text: str, source: str) -> list[dict]:
    """Split on every heading level (H1-H4), not just H2.

    This is a structural proxy for "topic boundary", not an embedding- or
    LLM-based segmenter -- that would need a model call per chunk, which
    conflicts with the no-frameworks constraint and this file's line
    budget. A document's headings are already where its author marked
    topic boundaries, so splitting on all of them is the honest
    stdlib-only approximation of "semantic".
    """
    return _split_on_headings(text, source, levels={1, 2, 3, 4}, strategy="semantic")


STRATEGIES = {"fixed": chunk_fixed, "header": chunk_header, "semantic": chunk_semantic}


def chunk_document(path: str, strategy: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return STRATEGIES[strategy](text, path)


def chunk_corpus(docs_dir: str, strategy: str) -> list[dict]:
    chunks = []
    for path in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
        chunks.extend(chunk_document(path, strategy))
    return chunks


def _preview(text: str, limit: int = 100) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", required=True, choices=sorted(STRATEGIES))
    parser.add_argument("--doc", help="Path to a single markdown file. Defaults to the whole corpus.")
    parser.add_argument("--docs-dir", default="docs")
    args = parser.parse_args()

    if args.doc:
        chunks = chunk_document(args.doc, args.strategy)
        label = args.doc
    else:
        chunks = chunk_corpus(args.docs_dir, args.strategy)
        label = args.docs_dir

    print(f"[{args.strategy}] {label} — {len(chunks)} chunks\n")
    for i, chunk in enumerate(chunks):
        path = " > ".join(chunk["headers"]) if chunk["headers"] else "(no header)"
        print(f"[{i}] {path}")
        print(f"    {_preview(chunk['text'])}")
        print(f"    ({len(chunk['text'])} chars)\n")


if __name__ == "__main__":
    main()
