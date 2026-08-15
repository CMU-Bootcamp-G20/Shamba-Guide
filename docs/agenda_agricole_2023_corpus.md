# Agenda Agricole 2023 — ShambaGuide corpus

## Purpose

This is the first real Kinyarwanda agricultural knowledge corpus prepared for ShambaGuide's retrieval layer.

## Source

- Source ID: `rab-agenda-agricole-2023`
- Title: `Agenda Agricole 2023`
- Organization: `MINAGRI/RAB`
- Year: `2023`
- Language: `rw`
- Uploaded source: `Agenda_Agricole_2023.pdf`

## Scope of this first pass

- Included printed pages: **84–258**.
- Pages 84–104: general crop/agricultural guidance, especially soil conservation and fertilizer.
- Pages 105–258: crop-specific guidance available in the source.
- Livestock/animal-production material is outside this corpus and is intentionally not included by the extraction boundary.

## Crop coverage detected

- ibigori
- ingano
- ibishyimbo
- soya
- umuceri
- urutoki
- ibirayi
- imyumbati
- inyanya
- ibitunguru
- imiteja
- ikawa
- icyayi
- general_agriculture

This is **not** a claim that ShambaGuide supports every crop in Rwanda. It is simply the set of crop sections successfully identified in this source pass.

## Data format

`agenda_agricole_2023_corpus.jsonl` contains one JSON object per retrieval chunk with:

- `document_id`
- `source_id`
- `title`
- `organization`
- `year`
- `language`
- `crop`
- `section`
- `page`
- `content_type`
- `text`

## Important boundary

This corpus preserves source evidence. It does **not** create or modify deterministic safety rules. Pesticide names/dosages present in the source remain source evidence and must not automatically become application rules.

## Current extraction method

1. Extract PDF text with `pdfplumber`.
2. Remove isolated page-number artifacts and whitespace noise.
3. Deduplicate repeated PDF pages/chunks.
4. Track crop only from crop-section headings, not incidental crop mentions.
5. Split page text into bounded retrieval chunks while preserving page and section metadata.
6. Validate the JSONL before indexing.
