"""
Embed Knowledge/FunnelOfTheWeek/vectorstore/chunks.jsonl and store in a local,
persistent ChromaDB collection - no external API, no per-token cost.

Uses ChromaDB's bundled default embedding function (a small MiniLM
model run locally via onnxruntime, downloaded once to ~/.cache on
first use). Good enough quality for first-pass retrieval; swap in a
different embedding_functions.* if quality needs improve later - the
rest of the pipeline (chunks.jsonl, metadata schema) does not change.
"""
import json
from pathlib import Path

import chromadb

CHUNKS_FILE = Path(r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore\chunks.jsonl")
PERSIST_DIR = r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore\chroma"
COLLECTION_NAME = "offers_funnel_analysis"
BATCH_SIZE = 100


def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # Fresh build each run - drop and recreate so re-running after an
    # extract/chunk change never leaves stale rows behind.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    ids, docs, metas = [], [], []
    n_total = 0
    n_indexed = 0

    with CHUNKS_FILE.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            n_total += 1
            if rec.get("is_image_only") or not rec["text"].strip():
                continue

            chunk_id = f"{rec['brand']}::{rec['lesson_id']}::{rec['chunk_index']}"
            ids.append(chunk_id)
            docs.append(rec["text"])
            metas.append({
                "brand": rec["brand"],
                "slug": rec["slug"],
                "title": rec["title"] or "",
                "order": rec["order"] or "",
                "lesson_id": rec["lesson_id"] or "",
                "created_at": rec["created_at"] or "",
                "chunk_index": rec["chunk_index"],
                "chunk_count": rec["chunk_count"],
                "source_path": rec["source_path"],
            })
            n_indexed += 1

            if len(ids) >= BATCH_SIZE:
                collection.add(ids=ids, documents=docs, metadatas=metas)
                ids, docs, metas = [], [], []
                print(f"  ...{n_indexed} chunks embedded so far")

    if ids:
        collection.add(ids=ids, documents=docs, metadatas=metas)

    print(f"OK: {n_indexed}/{n_total} chunk records embedded into "
          f"collection '{COLLECTION_NAME}' at {PERSIST_DIR}")
    print(f"Total in collection now: {collection.count()}")


if __name__ == "__main__":
    main()
