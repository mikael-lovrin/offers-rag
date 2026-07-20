"""
Semantic-ish chunking of Knowledge/FunnelOfTheWeek/vectorstore/corpus.jsonl
(one record per source lesson) into retrieval-sized chunks.

Strategy: each source text is already line-oriented (one paragraph or
bullet per line, see extract.py). We accumulate whole lines into a
chunk until adding the next line would exceed TARGET_CHARS, never
splitting a line/bullet mid-sentence. A short trailing overlap (the
last OVERLAP_LINES lines of a chunk) is repeated at the start of the
next chunk so a fact split across chunk boundaries still has context
on both sides.

Records with near-empty text (image-only lessons, e.g. bare
"landing-page" screenshots with no OCR yet) are kept as a single
"metadata-only" chunk (empty text marked explicitly) so they remain
discoverable by brand/slug even though there's nothing to embed
meaningfully - a future OCR pass can backfill real text without
changing this script's output shape.

Output: Knowledge/FunnelOfTheWeek/vectorstore/chunks.jsonl
"""
import json
from pathlib import Path

IN_FILE = Path(r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore\corpus.jsonl")
OUT_FILE = Path(r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore\chunks.jsonl")

TARGET_CHARS = 1000
MIN_CHARS_TO_CHUNK = 30
OVERLAP_LINES = 2


def chunk_text(text: str) -> list:
    lines = [l for l in text.split("\n") if l.strip() != ""]
    if not lines:
        return []

    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current and current_len + line_len > TARGET_CHARS:
            chunks.append("\n".join(current))
            current = current[-OVERLAP_LINES:] if OVERLAP_LINES else []
            current_len = sum(len(l) + 1 for l in current)
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def main():
    out_records = []
    n_source = 0
    n_empty = 0

    with IN_FILE.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            n_source += 1
            base_meta = {
                "brand": rec["brand"],
                "slug": rec["slug"],
                "title": rec["title"],
                "order": rec["order"],
                "lesson_id": rec["lesson_id"],
                "created_at": rec["created_at"],
                "attachment_count": rec["attachment_count"],
                "source_path": rec["source_path"],
            }

            if rec["char_count"] < MIN_CHARS_TO_CHUNK:
                n_empty += 1
                out_records.append({
                    **base_meta,
                    "chunk_index": 0,
                    "chunk_count": 1,
                    "text": "",
                    "is_image_only": True,
                })
                continue

            pieces = chunk_text(rec["text"])
            for i, piece in enumerate(pieces):
                out_records.append({
                    **base_meta,
                    "chunk_index": i,
                    "chunk_count": len(pieces),
                    "text": piece,
                    "is_image_only": False,
                })

    with OUT_FILE.open("w", encoding="utf-8") as out:
        for r in out_records:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    real_chunks = sum(1 for r in out_records if not r["is_image_only"])
    print(f"OK: {n_source} source lessons -> {len(out_records)} chunk records "
          f"({real_chunks} with real text, {n_empty} image-only placeholders)")
    print(f"Written to {OUT_FILE}")


if __name__ == "__main__":
    main()
