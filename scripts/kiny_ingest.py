import pymupdf
import json
import re
from pathlib import Path

RAW_DOC_PATH = "resources/raw_docs/imfashanyigisho.pdf"
OUTPUT_PATH = "resources/processed/corpus_kiny.jsonl"

# Keyword indicators for each crop in the RAB manual
CROP_KEYWORDS = {
    "IBIGORI": "maize",
    "IMYUMBATI": "cassava",
    "URUTOKI": "banana",
    "UMUCERI": "rice",
    "INTORYI": "garden_egg",
    "PUWAVURO": "bell_pepper",
    "POIVRON": "bell_pepper"
}

QUESTION_HEADING_PATTERN = re.compile(r"(?m)^([A-ZÀ-Ÿ0-9\s\?,\.’'’]{10,})$")

def clean_text(text: str) -> str:
    text = re.sub(r"Hamagara 4676, Umurongo utishyurwa wa\s*RAB", "", text)
    text = re.sub(r"\[PAGE\d+\]", "", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def build_corpus():
    doc = pymupdf.open(RAW_DOC_PATH)
    
    # Step 1: Collect text per page (Skipping pages 1-4 which are covers & TOC)
    pages_data = []
    for i in range(4, len(doc)):
        text = doc[i].get_text()
        pages_data.append({"page": i + 1, "text": text})
    doc.close()

    full_text = ""
    for p in pages_data:
        full_text += f"\n[PAGE{p['page']}]\n" + p['text']

    # Step 2: Track active crop as we scan through the text
    # Splitting full text into chunks based on double newlines / headers
    lines = full_text.split('\n')
    
    current_crop = None
    current_page = 5
    current_chunk_lines = []
    all_chunks = []
    chunk_id = 0
    seen_texts = set()

    for line in lines:
        clean_line = line.strip()
        
        # Track page numbers
        page_match = re.match(r"\[PAGE(\d+)\]", clean_line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        # Check if line indicates a new crop chapter
        upper_line = clean_line.upper()
        for kw, crop_code in CROP_KEYWORDS.items():
            if kw in upper_line and "IMFASHANYIGISHO" in upper_line:
                current_crop = crop_code
                print(f"-> Detected chapter for: {crop_code} (Page {current_page})")
                break

        # Accumulate text into chunks
        if clean_line:
            current_chunk_lines.append(clean_line)
            
        # Create a chunk when we hit a large paragraph pause or question mark
        if len(current_chunk_lines) > 5 or (clean_line.endswith('?') and len(current_chunk_lines) > 2):
            text_block = clean_text(" ".join(current_chunk_lines))
            
            if current_crop and len(text_block) > 50 and text_block not in seen_texts:
                seen_texts.add(text_block)
                all_chunks.append({
                    "chunk_id": f"rab_{current_crop}_{chunk_id:04d}",
                    "crop": current_crop,
                    "source": "RAB_ABAJYANAMA_2021A",
                    "page": current_page,
                    "language": "rw",
                    "text": text_block,
                })
                chunk_id += 1
            current_chunk_lines = []

    Path("resources/processed").mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"\nSUCCESS: Extracted {len(all_chunks)} chunks across all crops to {OUTPUT_PATH}")

if __name__ == "__main__":
    build_corpus()