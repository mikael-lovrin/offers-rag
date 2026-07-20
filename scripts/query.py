"""
Query tool for the local Offers RAG - human-readable by default,
machine-readable with --json (for other agents/scripts to shell out to).

Usage:
  .venv\\Scripts\\python.exe scripts\\query.py "your question here" [--n N] [--brand slug] [--json]
"""
import argparse
import json
import sys

import chromadb

PERSIST_DIR = r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore\chroma"
COLLECTION_NAME = "offers_funnel_analysis"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--brand", default=None, help="filter to a single brand slug (folder name under Offers/raw)")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON instead of formatted text")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = client.get_collection(COLLECTION_NAME)
    where = {"brand": args.brand} if args.brand else None
    result = collection.query(query_texts=[args.query], n_results=args.n, where=where)

    ids = result["ids"][0]
    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result["distances"][0]

    if args.json:
        out = [
            {"rank": i + 1, "id": id_, "distance": dist, "text": doc, **meta}
            for i, (id_, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists))
        ]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    for rank, (id_, doc, meta, dist) in enumerate(zip(ids, docs, metas, dists), 1):
        print(f"\n=== #{rank} | dist={dist:.4f} | brand={meta['brand']} | slug={meta['slug']} | title={meta['title']!r}")
        print(doc[:350].replace("\n", " | "))


if __name__ == "__main__":
    main()
