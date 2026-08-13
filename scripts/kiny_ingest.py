import pymupdf
import json
import re
from pathlib import Path

RAW_DOC_PATH = "resources/raw_docs/imfashanyigisho.pdf"
OUTPUT_PATH = "resources/processed/corpus_kiny.jsonl"

# Maps the exact crop-name fragment as it appears in the chapter title to your crop tag
CHAPTER_TITLE_TO_CROP = {
    "IBIGORI": "maize",
    "IMYUMBATI": "cassava",
    "URUTOKI": "banana",
    "UMUCERI": "rice",
    "INTORYI": "garden_egg",
    "PUWAVURO": "bell_pepper",
}

CHAPTER_TITLE_PATTERN = re.compile(
    r"IMFASHANYIGISHO Y[’']? AMAHUGURWA KU BUHINZI BWA KIJYAMBERE BWA?[’']?\s*([A-Z]+)"
)
QUESTION_HEADING_PATTERN = re.compile(r"(?m)^([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\?,\.’']{10,})$")

def extract_full_text(doc_path):
    doc = pymupdf.open(doc_path)
    full_text = ""
    for i, page in enumerate(doc):
        full_text += f"\n[PAGE{i+1}]\n" + page.get_text()
    doc.close()
    return full_text

def clean_text(text: str) -> str:
    text = re.sub(r"Hamagara 4676, Umurongo utishyurwa wa\s*RAB", "", text)
    text = re.sub(r"\[PAGE\d+\]", "", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def find_page_for_offset(full_text, offset):
    markers = list(re.finditer(r"\[PAGE(\d+)\]", full_text[:offset]))
    return int(markers[-1].group(1)) if markers else -1

def split_into_crop_chapters(full_text):
    matches = list(CHAPTER_TITLE_PATTERN.finditer(full_text))
    chapters = []
    for idx, m in enumerate(matches):
        crop = CHAPTER_TITLE_TO_CROP.get(m.group(1))
        if not crop:
            continue
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)
        chapters.append({"crop": crop, "text": full_text[start:end]})
    return chapters

def split_into_qa_chunks(chapter_text, crop, full_text_offset_base):
    headings = list(QUESTION_HEADING_PATTERN.finditer(chapter_text))
    chunks = []
    for idx, h in enumerate(headings):
        start = h.start()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(chapter_text)
        raw = chapter_text[start:end]
        page = find_page_for_offset(chapter_text, start) 
        chunks.append({"crop": crop, "page": page, "text": clean_text(raw)})
    return chunks

def build_corpus():
    full_text = extract_full_text(RAW_DOC_PATH)

    chapter_matches = list(CHAPTER_TITLE_PATTERN.finditer(full_text))
    print("Chapter titles found:", [m.group(1) for m in chapter_matches])  # debug: check PUWAVURO shows up here

    question_matches = list(QUESTION_HEADING_PATTERN.finditer(full_text))

    all_chunks, chunk_id = [], 0
    for c_idx, c_match in enumerate(chapter_matches):
        crop = CHAPTER_TITLE_TO_CROP.get(c_match.group(1))
        if not crop:
            continue
        chapter_start = c_match.start()
        chapter_end = chapter_matches[c_idx + 1].start() if c_idx + 1 < len(chapter_matches) else len(full_text)

        headings_in_chapter = [h for h in question_matches if chapter_start <= h.start() < chapter_end]
        for h_idx, h in enumerate(headings_in_chapter):
            start = h.start()
            end = headings_in_chapter[h_idx + 1].start() if h_idx + 1 < len(headings_in_chapter) else chapter_end
            page = find_page_for_offset(full_text, start)  # absolute offset now, not chapter-relative
            text = clean_text(full_text[start:end])
            if len(text) < 40:
                continue
            all_chunks.append({
                "chunk_id": f"rab_{crop}_{chunk_id:04d}",
                "crop": crop, "source": "RAB_ABAJYANAMA_2021A",
                "page": page, "language": "rw", "text": text,
            })
            chunk_id += 1

    Path("resources/processed").mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(all_chunks)} chunks to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_corpus()

# Quick diagnostic, not part of the main pipeline, just to see what's really on that page
doc = pymupdf.open("resources/raw_docs/imfashanyigisho.pdf")
for i in range(17, 20):  # pages around where puwavuro should be, 0-indexed
    print(f"--- page {i+1} ---")
    print(doc[i].get_text()[:500])