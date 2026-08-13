import pymupdf
import json
import re
from pathlib import Path

RAW_DOC_PATH = "resources/raw_docs/pmp.pdf"
OUTPUT_PATH = "resources/processed/corpus.jsonl"

# Chapter 3 as a whole, we split it internally by heading instead of by page range
CHAPTER_START, CHAPTER_END = 31, 68

HEADING_PATTERN = re.compile(r'(?m)^(3\.\d+(?:\.\d+)?)\s+([A-Z][^\n]{2,80})$')

HEADING_TO_CROP = {
    "3.2": "maize", "3.2.1": "maize", "3.2.2": "maize",
    "3.3": "irish_potato", "3.3.1": "irish_potato", "3.3.2": "irish_potato",
    "3.5.2": "tomato",
    "3.6": "beans", "3.6.1": "beans", "3.6.2": "beans",
}

def extract_with_page_markers(doc_path, start_page, end_page):
    doc = pymupdf.open(doc_path)
    full_text = ""
    for i in range(start_page - 1, end_page):
        full_text += f"\n[PAGE{i+1}]\n" + doc[i].get_text()
    doc.close()
    return full_text

def clean_text(text: str) -> str:
    text = re.sub(
        r"Commercialization and De-Risking for Agricultural Transformation \(CDAT\) Project PMP",
        "", text
    )
    text = re.sub(r"Page\s*\d+", "", text)          # fixed: \s* catches "Page31" with no space
    text = re.sub(r"\[PAGE\d+\]", "", text)          # strip our own page markers before saving
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def find_page_for_offset(full_text: str, offset: int) -> int:
    markers = list(re.finditer(r"\[PAGE(\d+)\]", full_text[:offset]))
    return int(markers[-1].group(1)) if markers else -1

def split_by_heading(full_text: str) -> list[dict]:
    matches = list(HEADING_PATTERN.finditer(full_text))
    sections = []
    for idx, m in enumerate(matches):
        heading_num = m.group(1)
        crop = HEADING_TO_CROP.get(heading_num)
        if not crop:
            continue
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        page = find_page_for_offset(full_text, start)
        sections.append({
            "crop": crop, "heading": heading_num,
            "page": page, "text": clean_text(full_text[start:end]),
        })
    return sections

def chunk_section(text: str, max_len: int = 500) -> list[str]:
    # sentence-aware splitting so a chunk doesn't exceed max_len mid-thought
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) > max_len and current:
            chunks.append(current.strip())
            current = s
        else:
            current += " " + s
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if len(c) >= 60]

def build_corpus():
    full_text = extract_with_page_markers(RAW_DOC_PATH, CHAPTER_START, CHAPTER_END)
    sections = split_by_heading(full_text)

    all_chunks = []
    chunk_id = 0
    for section in sections:
        for chunk_text in chunk_section(section["text"]):
            all_chunks.append({
                "chunk_id": f"pmp_{section['crop']}_{chunk_id:04d}",
                "crop": section["crop"],
                "source": "RAB_PMP_2022",
                "heading": section["heading"],
                "page": section["page"],
                "language": "en",
                "text": chunk_text,
            })
            chunk_id += 1

    Path("resources/processed").mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(all_chunks)} chunks to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_corpus()