"""Embed chunks and a query, return top-k by cosine similarity.

Run standalone to preview retrieval for one query:
    python eval/retrieve.py --query "how do I change the alert threshold" --strategy header --top-k 3

Requires VOYAGE_API_KEY in the environment. In CI this comes from a repo
secret injected as an env var -- no key ever lives in this file or in
config.
"""
import argparse
import math
import os

import voyageai

from chunk import STRATEGIES, chunk_corpus

MODEL = "voyage-3.5"


def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return client.embed(texts, model=MODEL, input_type=input_type).embeddings


def build_index(chunks: list[dict]) -> list[dict]:
    """Embed every chunk once and attach the vector. This list is the
    whole index -- no vector DB, which is correct at this scale."""
    vectors = embed_texts([c["text"] for c in chunks])
    return [{**c, "embedding": v} for c, v in zip(chunks, vectors)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def top_k(query: str, index: list[dict], k: int = 5) -> list[dict]:
    """Embed the query once, score it against every chunk in the index,
    and return the top k -- with the embedding vector stripped back out,
    so nothing downstream (printing, judge.py) ever sees a raw vector."""
    query_vector = embed_texts([query], input_type="query")[0]
    scored = []
    for chunk in index:
        hit = {key: value for key, value in chunk.items() if key != "embedding"}
        hit["score"] = cosine_similarity(query_vector, chunk["embedding"])
        scored.append(hit)
    scored.sort(key=lambda hit: hit["score"], reverse=True)
    return scored[:k]


def _preview(text: str, limit: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--strategy", required=True, choices=sorted(STRATEGIES))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--docs-dir", default="docs")
    args = parser.parse_args()

    chunks = chunk_corpus(args.docs_dir, args.strategy)
    index = build_index(chunks)
    hits = top_k(args.query, index, k=args.top_k)

    print(f"Query: {args.query}")
    print(f"Strategy: {args.strategy} · {len(chunks)} chunks indexed\n")
    for i, hit in enumerate(hits, start=1):
        headers = " > ".join(hit["headers"]) if hit["headers"] else "(no header)"
        print(f"{i}. {hit['score']:.3f}  {hit['source']:<40} {headers}")
        print(f"   \"{_preview(hit['text'])}\"")


if __name__ == "__main__":
    main()
