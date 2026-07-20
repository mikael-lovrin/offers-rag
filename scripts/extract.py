"""
Extract clean text + metadata from Funnel of the Week raw JSON exports
(Knowledge/FunnelOfTheWeek/raw/<brand>/raw-api/<order>_<lesson_id>_<slug>.json).

Each raw file is a Circle.so "lesson" API object, double-JSON-encoded
(the file content is a JSON string literal containing escaped JSON).
The rich text body is a ProseMirror-style doc tree
(serialized_rich_text_body.body.content -> paragraph/bulletList/heading/...).

We walk that tree ourselves instead of using the bundled
`circle_ios_fallback_text` field, because that field sometimes
concatenates adjacent blocks with no separator (observed run-on text
between a bullet list and the following paragraph), which would hurt
chunk quality.

Output: one JSON object per line (JSONL) to
Knowledge/FunnelOfTheWeek/vectorstore/corpus.jsonl
"""
import json
import re
import sys
from pathlib import Path

RAW_ROOT = Path(r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\raw")
OUT_DIR = Path(r"C:\Users\mikae\FEG\Knowledge\FunnelOfTheWeek\vectorstore")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "corpus.jsonl"

FILENAME_RE = re.compile(r"^(\d+)_(\d+)_(.+)\.json$", re.IGNORECASE)


def load_double_encoded(path: Path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)
    if isinstance(data, str):
        data = json.loads(data)
    return data


def node_text(node) -> str:
    """Flatten a single inline node (text / hardBreak) to a string, appending link URLs once."""
    if node.get("type") == "hardBreak":
        return "\n"
    text = node.get("text", "") or ""
    marks = node.get("marks") or []
    for m in marks:
        if m.get("type") == "link":
            href = (m.get("attrs") or {}).get("href")
            if href and href not in text:
                text = f"{text} ({href})"
    return text


def block_to_lines(node, depth=0) -> list:
    """Walk a ProseMirror-style block node, return a list of plain-text lines."""
    t = node.get("type")
    content = node.get("content") or []

    if t in ("paragraph", "heading"):
        line = "".join(node_text(c) for c in content if c.get("type") in ("text", "hardBreak"))
        line = line.strip()
        if not line:
            return []
        if t == "heading":
            level = (node.get("attrs") or {}).get("level", 2)
            return ["#" * level + " " + line]
        return [line]

    if t == "bulletList" or t == "orderedList":
        lines = []
        for li in content:
            sub_lines = []
            for child in li.get("content") or []:
                sub_lines.extend(block_to_lines(child, depth + 1))
            if sub_lines:
                first, *rest = sub_lines
                lines.append(f"- {first}")
                lines.extend(f"  {r}" for r in rest)
        return lines

    if t == "horizontalRule":
        return ["---"]

    if t == "codeBlock":
        code_text = "".join(node_text(c) for c in content if c.get("type") == "text")
        return [code_text] if code_text.strip() else []

    if t in ("blockquote",):
        lines = []
        for child in content:
            lines.extend(block_to_lines(child, depth + 1))
        return [f"> {l}" for l in lines]

    # Unknown block container (e.g. custom embed types) - recurse into children if any
    if content:
        lines = []
        for child in content:
            lines.extend(block_to_lines(child, depth + 1))
        return lines
    return []


def extract_plain_text(lesson: dict) -> str:
    srb = lesson.get("serialized_rich_text_body") or lesson.get("rich_text_body") or {}
    body = srb.get("body") or {}
    content = body.get("content") or []
    lines = []
    for node in content:
        lines.extend(block_to_lines(node))
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_attachments(lesson: dict) -> list:
    srb = lesson.get("serialized_rich_text_body") or lesson.get("rich_text_body") or {}
    names = []
    for key in ("attachments", "inline_attachments"):
        for a in srb.get(key) or []:
            fn = a.get("filename")
            if fn:
                names.append(fn)
    return names


def main():
    records = []
    skipped = []
    for brand_dir in sorted(RAW_ROOT.iterdir()):
        if not brand_dir.is_dir():
            continue
        brand = brand_dir.name
        api_dir = brand_dir / "raw-api"
        if not api_dir.exists():
            continue
        for f in sorted(api_dir.glob("*.json")):
            m = FILENAME_RE.match(f.name)
            order, lesson_id, slug = (m.group(1), m.group(2), m.group(3)) if m else (None, None, f.stem)
            try:
                lesson = load_double_encoded(f)
            except Exception as e:
                skipped.append((str(f), f"parse_error: {e}"))
                continue
            if not isinstance(lesson, dict):
                skipped.append((str(f), "not_a_dict_after_decode"))
                continue

            title = lesson.get("name", "") or ""
            created_at = lesson.get("created_at")
            text = extract_plain_text(lesson)
            attachments = extract_attachments(lesson)

            records.append({
                "brand": brand,
                "order": order,
                "lesson_id": lesson_id,
                "slug": slug,
                "title": title,
                "created_at": created_at,
                "text": text,
                "char_count": len(text),
                "attachment_count": len(attachments),
                "attachment_filenames": attachments,
                "source_path": str(f.relative_to(RAW_ROOT.parent.parent)),
            })

    with OUT_FILE.open("w", encoding="utf-8") as out:
        for r in records:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"OK: {len(records)} records written to {OUT_FILE}")
    empty = sum(1 for r in records if r["char_count"] < 30)
    print(f"  {empty} records have near-empty text (<30 chars) - likely image-only lessons")
    print(f"  {len(skipped)} files skipped/failed to parse")
    if skipped:
        for path, reason in skipped[:20]:
            print(f"    SKIP {path}: {reason}")
        if len(skipped) > 20:
            print(f"    ... and {len(skipped) - 20} more (see full run output)")


if __name__ == "__main__":
    main()
