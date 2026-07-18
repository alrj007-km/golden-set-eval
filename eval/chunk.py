"""Three chunking strategies over a markdown corpus. CLI:
    python eval/chunk.py --strategy semantic --doc docs/api-reference.md
"""
import argparse
import glob
import os
import re

# Word count, not a real token count -- avoids a tokenizer dependency for
# three strategies over four documents. An approximation, not an oversight.
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
    # Skips fenced code blocks -- several docs use "#" for shell/Python
    # comments inside code samples, which aren't markdown headings.
    max_tracked = max(levels)
    chunks: list[dict] = []
    header_stack: dict[int, str] = {}
    current_lines: list[str] = []
    in_fence = False

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append({
                "chunk_id": f"{source}#{len(chunks)}",
                "source": source,
                "text": body,
                "headers": [header_stack[d] for d in sorted(header_stack)],
                "strategy": strategy,
            })

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            current_lines.append(line)
            continue
        match = None if in_fence else HEADER_RE.match(line)
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
    """Split on H2 boundaries only -- an H2 section keeps its H3s."""
    return _split_on_headings(text, source, {2}, "header")

def chunk_semantic(text: str, source: str) -> list[dict]:
    # All heading levels (H1-H4), not just H2 -- a structural proxy for
    # "topic boundary". Not embedding- or LLM-based: that needs a model
    # call per chunk, which breaks the no-frameworks rule and this file's
    # line budget. Headings are where the author already marked topics.
    return _split_on_headings(text, source, {1, 2, 3, 4}, "semantic")

STRATEGIES = {"fixed": chunk_fixed, "header": chunk_header, "semantic": chunk_semantic}

def chunk_document(path: str, strategy: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return STRATEGIES[strategy](f.read(), path)

def chunk_corpus(docs_dir: str, strategy: str) -> list[dict]:
    chunks = []
    for path in sorted(glob.glob(os.path.join(docs_dir, "*.md"))):
        chunks.extend(chunk_document(path, strategy))
    return chunks

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", required=True, choices=sorted(STRATEGIES))
    parser.add_argument("--doc", help="Single file; defaults to the whole corpus.")
    parser.add_argument("--docs-dir", default="docs")
    args = parser.parse_args()

    chunks = chunk_document(args.doc, args.strategy) if args.doc else chunk_corpus(args.docs_dir, args.strategy)
    print(f"[{args.strategy}] {args.doc or args.docs_dir} — {len(chunks)} chunks\n")
    for i, chunk in enumerate(chunks):
        preview = " ".join(chunk["text"].split())[:100]
        suffix = "..." if len(chunk["text"]) > 100 else ""
        print(f"[{i}] {' > '.join(chunk['headers']) or '(no header)'}")
        print(f"    {preview}{suffix}  ({len(chunk['text'])} chars)\n")

if __name__ == "__main__":
    main()
