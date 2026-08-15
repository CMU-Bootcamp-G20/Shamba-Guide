from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = {
    "document_id", "source_id", "title", "organization", "year",
    "language", "crop", "section", "page", "content_type", "text"
}
ALLOWED_LANGUAGE = {"rw"}
FORBIDDEN_TERMS = ["inka", "inkoko", "ingurube", "ihene", "amatungo"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    args = ap.parse_args()

    rows = [json.loads(x) for x in args.input.read_text(encoding="utf-8").splitlines() if x.strip()]
    errors: list[str] = []
    ids: set[str] = set()
    texts: set[str] = set()

    for i, row in enumerate(rows, 1):
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"line {i}: missing {sorted(missing)}")
        if row.get("language") not in ALLOWED_LANGUAGE:
            errors.append(f"line {i}: language must be rw")
        if row.get("source_id") != "rab-agenda-agricole-2023":
            errors.append(f"line {i}: unexpected source_id")
        if not isinstance(row.get("page"), int) or not (84 <= row["page"] <= 258):
            errors.append(f"line {i}: page outside corpus scope")
        if row.get("document_id") in ids:
            errors.append(f"line {i}: duplicate document_id")
        ids.add(row.get("document_id"))
        normalized = " ".join(str(row.get("text", "")).lower().split())
        if normalized in texts:
            errors.append(f"line {i}: duplicate text")
        texts.add(normalized)
        # Only flag likely animal-production chunks; this is a review warning,
        # not an automatic deletion rule.
        if any(term in normalized for term in FORBIDDEN_TERMS):
            print(f"WARNING line {i}: possible livestock reference on page {row.get('page')}")

    print(f"Records checked: {len(rows)}")
    print(f"Unique document IDs: {len(ids)}")
    print(f"Unique texts: {len(texts)}")
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print("-", e)
        raise SystemExit(1)
    print("VALIDATION PASSED")


if __name__ == "__main__":
    main()
