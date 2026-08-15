from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TARGET_CHARS = 600
MIN_CHARS = 80
MAX_CHARS = 1000


def normalize_space(text: str) -> str:
    """Normalize horizontal whitespace while preserving line boundaries."""
    return re.sub(r"[ \t]+", " ", text).strip()


def split_long_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """
    Split a long block into pieces without exceeding max_chars.

    Prefer sentence boundaries. If a single sentence is still too long,
    fall back to whitespace boundaries and finally hard character splits.
    """
    text = normalize_space(text)

    if len(text) <= max_chars:
        return [text]

    # First try sentence boundaries.
    sentences = re.split(r"(?<=[.!?።])\s+", text)

    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = f"{current} {sentence}".strip() if current else sentence

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            pieces.append(current)
            current = ""

        # A single sentence may itself exceed max_chars.
        if len(sentence) <= max_chars:
            current = sentence
            continue

        # Try whitespace boundaries.
        words = sentence.split()
        word_piece = ""

        for word in words:
            candidate = f"{word_piece} {word}".strip() if word_piece else word

            if len(candidate) <= max_chars:
                word_piece = candidate
            else:
                if word_piece:
                    pieces.append(word_piece)

                # Extremely long token fallback.
                if len(word) > max_chars:
                    for start in range(0, len(word), max_chars):
                        pieces.append(word[start:start + max_chars])
                    word_piece = ""
                else:
                    word_piece = word

        if word_piece:
            current = word_piece

    if current:
        pieces.append(current)

    return [piece.strip() for piece in pieces if piece.strip()]


def split_page(
    text: str,
    target_chars: int = TARGET_CHARS,
    max_chars: int = MAX_CHARS,
) -> list[str]:
    """
    Split page content into retrieval-friendly chunks.

    Goals:
    - Prefer chunks around target_chars.
    - Normally keep chunks between ~400 and 800 characters.
    - Never exceed max_chars.
    - Preserve headings, bullets, and paragraph boundaries where possible.
    """
    raw_lines = [
        normalize_space(line)
        for line in text.splitlines()
        if normalize_space(line)
    ]

    # First expand any individual line that is itself too large.
    lines: list[str] = []

    for line in raw_lines:
        if len(line) <= max_chars:
            lines.append(line)
        else:
            lines.extend(split_long_text(line, max_chars))

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line)
        separator_len = 1 if current else 0

        # If adding this line would exceed the hard maximum,
        # finalize the current chunk first.
        if current and current_len + separator_len + line_len > max_chars:
            chunks.append("\n".join(current).strip())
            current = []
            current_len = 0

        # If the current chunk has reached the target range and adding
        # another line would make it substantially larger, finalize it.
        elif (
            current
            and current_len >= target_chars
            and current_len + separator_len + line_len > target_chars
        ):
            chunks.append("\n".join(current).strip())
            current = []
            current_len = 0

        current.append(line)
        current_len += line_len + (1 if len(current) > 1 else 0)

    if current:
        chunks.append("\n".join(current).strip())

    # Second pass: if a chunk is still too large, split it safely.
    final_chunks: list[str] = []

    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
        else:
            final_chunks.extend(split_long_text(chunk, max_chars))

    return [chunk.strip() for chunk in final_chunks if chunk.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()

    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)

    ap.add_argument(
        "--target-chars",
        type=int,
        default=TARGET_CHARS,
        help="Preferred chunk size. Default: 600",
    )

    ap.add_argument(
        "--max-chars",
        type=int,
        default=MAX_CHARS,
        help="Absolute maximum chunk size. Default: 1000",
    )

    args = ap.parse_args()

    if args.target_chars <= 0:
        raise ValueError("--target-chars must be greater than 0")

    if args.max_chars < args.target_chars:
        raise ValueError("--max-chars must be >= --target-chars")

    pages = [
        json.loads(line)
        for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    out: list[dict] = []
    seen: set[str] = set()

    for page in pages:
        parts = split_page(
            page["text"],
            target_chars=args.target_chars,
            max_chars=args.max_chars,
        )

        chunk_number = 1

        for text in parts:
            if len(text) < MIN_CHARS:
                continue

            # Prevent exact duplicate chunks caused by PDF extraction duplication.
            normalized_for_hash = re.sub(r"\s+", " ", text).lower()

            h = hashlib.sha1(
                normalized_for_hash.encode("utf-8")
            ).hexdigest()

            if h in seen:
                continue

            seen.add(h)

            record = {
                "document_id": (
                    f"{page['source_id']}"
                    f"-p{page['page']:03d}"
                    f"-c{chunk_number:02d}"
                ),
                "source_id": page["source_id"],
                "title": page["title"],
                "organization": page["organization"],
                "year": page["year"],
                "language": page["language"],
                "crop": page["crop"],
                "section": page["section"],
                "page": page["page"],
                "content_type": page["content_type"],
                "text": text,
            }

            out.append(record)
            chunk_number += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as f:
        for record in out:
            f.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    lengths = [len(record["text"]) for record in out]

    print(f"Wrote {len(out)} chunks to {args.output}")

    if lengths:
        print(f"Minimum chunk size: {min(lengths)}")
        print(f"Maximum chunk size: {max(lengths)}")
        print(f"Average chunk size: {sum(lengths) / len(lengths):.1f}")
        print(
            f"Chunks > {args.max_chars}: "
            f"{sum(length > args.max_chars for length in lengths)}"
        )


if __name__ == "__main__":
    main()