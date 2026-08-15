from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pdfplumber


SOURCE_ID = "rab-agenda-agricole-2023"
TITLE = "Agenda Agricole 2023"
LANGUAGE = "rw"
ORGANIZATION = "MINAGRI/RAB"

# The crop/agriculture portion starts at printed page 84 in the uploaded PDF.
# Livestock begins later; the first corpus pass deliberately stops before it.
DEFAULT_START = 84
DEFAULT_END = 258

# Crop names explicitly encountered in the Agenda. These are metadata labels,
# not translations invented by this script.
CROP_PATTERNS: list[tuple[str, str]] = [
    (r"\bIBIGORI\b", "ibigori"),
    (r"\bINGANO\b", "ingano"),
    (r"\bIBISHYIMBO\b", "ibishyimbo"),
    (r"\bSOYA\b", "soya"),
    (r"\bUMUCERI\b", "umuceri"),
    (r"\bIMYUMBATI\b", "imyumbati"),
    (r"\bURUTOKI\b", "urutoki"),
    (r"\bIBIRAYI\b", "ibirayi"),
    (r"\bINYANYA\b", "inyanya"),
    (r"\bIBITUNGURU\b", "ibitunguru"),
    (r"\bIMITEJA\b", "imiteja"),
    (r"\bAMASHU\b", "amashu"),
    (r"\bIKAWA\b", "ikawa"),
    (r"\bICYAYI\b", "icyayi"),
    (r"\bIMYEMBE\b", "imyembe"),
    (r"\bAVOCAT\b|\bAVOCADO\b", "avoka"),
]

# Broad headings we want to preserve as sections. This is deliberately
# conservative: the source text remains the authority.
HEADING_PATTERNS = [
    r"^KUBUNGABUNGA UBUTAKA$",
    r"^GUKORESHA INGARANE$",
    r"^GUKORA IKIRUNDO$",
    r"^UBUHINZI BWA KIJYAMBERE",
    r"^A\. IBIGORI$",
    r"^B\. INGANO$",
    r"^C\. IBISHYIMBO$",
    r"^D\. SOYA$",
    r"^E\. UMUCERI$",
    r"^F\. IMYUMBATI$",
    r"^G\. URUTOKI$",
    r"^K\. IBIRAYI$",
    r"^C\. INYANYA$",
    r"^D\. IBITUNGURU$",
    r"^INDWARA N’IBYONNYI",
    r"^INDWARA N'IBYONNYI",
    r"^INDWARA N’IBYONNYI BY’INGENZI",
    r"^INDWARA N'IBYONNYI BY'INGENZI",
]

# Add this function near the top of the file, after the imports
from collections import defaultdict

def extract_page_text(page, x_split: float = 0) -> str:
    """Extract words by position instead of pdfplumber's default line reconstruction.
    Drops any word starting left of x_split, this document embeds a duplicate
    copy of the previous page's tail content at negative x-coordinates, which
    was getting woven into each page's real content. Rebuilding lines from
    word positions ourselves also fixes most (not all) missing-space issues
    that page.extract_text() introduces on tight kerning.
    """
    words = page.extract_words(x_tolerance=2, y_tolerance=3)
    words = [w for w in words if w["x0"] >= x_split]
    lines = defaultdict(list)
    for w in words:
        lines[round(w["top"])].append(w)
    out_lines = []
    for t in sorted(lines.keys()):
        row = sorted(lines[t], key=lambda w: w["x0"])
        out_lines.append(" ".join(w["text"] for w in row))
    return "\n".join(out_lines)

def clean_line(line: str) -> str:
    line = line.replace("\u00a0", " ")
    line = line.replace("\ufb01", "fi").replace("\ufb02", "fl")
    line = re.sub(r"\s+", " ", line).strip()
    return line


def clean_text(text: str) -> str:
    # Remove repeated printed page number at beginning/end where it is isolated.
    lines = [clean_line(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    # Remove a line consisting only of a page number.
    lines = [x for x in lines if not re.fullmatch(r"\d{1,3}", x)]
    return "\n".join(lines).strip()


def normalized_for_hash(text: str) -> str:
    # Used only for detecting duplicate PDF pages. We do not alter stored text.
    s = re.sub(r"\s+", " ", text).lower()
    s = re.sub(r"\b\d{1,3}\b", " ", s)
    return s.strip()


def detect_crop(text: str, current_crop: str | None) -> str | None:
    """Update crop only when a crop section heading appears.

    A crop name mentioned inside ordinary prose must not change the page
    metadata (e.g. maize is mentioned in the soil-conservation section).
    """
    upper = text.upper()
    heading_patterns = [
        (r"\bA\.\s*IBIGORI\b", "ibigori"),
        (r"\bB\.\s*INGANO\b", "ingano"),
        (r"\bD\.\s*IBISHYIMBO\b", "ibishyimbo"),
        (r"\bE\.\s*SOYA\b", "soya"),
        (r"\bC\.\s*UMUCERI\b", "umuceri"),
        (r"\bF\.\s*URUTOKI\b", "urutoki"),
        (r"\bK\.\s*IBIRAYI\b", "ibirayi"),
        (r"\bL\.\s*IMYUMBATI\b", "imyumbati"),
        (r"\bC\.\s*INYANYA\b", "inyanya"),
        (r"\bD\.\s*IBITUNGURU\b", "ibitunguru"),
        (r"\bG\.\s*IMITEJA\b", "imiteja"),
        (r"\bA\.\s*IKAWA\b", "ikawa"),
        (r"\bB\.\s*ICYAYI\b", "icyayi"),
    ]
    for pattern, crop in heading_patterns:
        if re.search(pattern, upper):
            return crop
    return current_crop

def detect_section(text: str, current_section: str | None) -> str | None:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:12]:
        normalized = re.sub(r"\s+", " ", line).strip()
        upper = normalized.upper()
        for pattern in HEADING_PATTERNS:
            if re.search(pattern, upper):
                return normalized
    return current_section


def classify_content(text: str) -> str:
    u = text.upper()
    if "INDWARA" in u or "IBYONNYI" in u or "IBIMENYETSO" in u:
        return "pest_disease"
    if "IFUMBIRE" in u or "GUFUMBIRA" in u or "NPK" in u or "UREA" in u:
        return "soil_fertilizer"
    if "GUSARURA" in u or "GUHUNIKA" in u or "UMUSARURO" in u:
        return "harvest_postharvest"
    if "KUBUNGABUNGA UBUTAKA" in u or "ISURI" in u or "GUKORESHA INGARANE" in u:
        return "soil_conservation"
    return "crop_production"


def extract(pdf_path: Path, start_page: int, end_page: int) -> list[dict]:
    records: list[dict] = []
    previous_hash: str | None = None
    current_crop: str | None = None
    current_section: str | None = None

    with pdfplumber.open(pdf_path) as pdf:
        end_page = min(end_page, len(pdf.pages))
        for printed_page in range(start_page, end_page + 1):
            page = pdf.pages[printed_page - 1]
            raw = extract_page_text(page) or ""
            text = clean_text(raw)
            if not text:
                continue

            h = hashlib.sha1(normalized_for_hash(text).encode("utf-8")).hexdigest()
            if h == previous_hash:
                continue
            previous_hash = h

            current_crop = detect_crop(text, current_crop)
            if current_crop is None and printed_page < 105:
                current_crop = "general_agriculture"
            current_section = detect_section(text, current_section)

            # Exclude animal-production material if it appears before our hard stop.
            # This is a safeguard, not the primary boundary.
            u = text.upper()
            if any(term in u for term in ["KUGABURIRA INKA", "KORORA INKA", "UBWOROZI BW’INKA", "UBWOROZI BW'INKA"]):
                continue

            records.append(
                {
                    "document_id": f"{SOURCE_ID}-p{printed_page:03d}",
                    "source_id": SOURCE_ID,
                    "title": TITLE,
                    "organization": ORGANIZATION,
                    "year": 2023,
                    "language": LANGUAGE,
                    "crop": current_crop,
                    "section": current_section,
                    "page": printed_page,
                    "content_type": classify_content(text),
                    "text": text,
                }
            )

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract the crop/agriculture portion of Agenda Agricole 2023.")
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start-page", type=int, default=DEFAULT_START)
    parser.add_argument("--end-page", type=int, default=DEFAULT_END)
    args = parser.parse_args()

    records = extract(args.pdf, args.start_page, args.end_page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} unique page records to {args.output}")


if __name__ == "__main__":
    main()
