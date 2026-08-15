from __future__ import annotations

import argparse
import json
from pathlib import Path

import warnings
import torch
import transformers

try:
    import colbert.modeling.colbert
    colbert.modeling.colbert.ColBERT.try_load_torch_extensions = lambda *args, **kwargs: None
except ImportError:
    pass

from ragatouille import RAGPretrainedModel

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
torch.set_default_device("cpu")
transformers.AdamW = torch.optim.AdamW

MODEL_NAME = "C4IR-RW/kiny-colbert-free"
INDEX_NAME = "shambaguide_kinya_agenda_2023"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a ColBERT index from the curated Agenda Agricole corpus.")
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--index-name", default=INDEX_NAME)
    args = ap.parse_args()

    records = load_jsonl(args.corpus)
    if not records:
        raise SystemExit("Corpus is empty")

    collection = [r["text"] for r in records]
    document_ids = [r["document_id"] for r in records]
    metadatas = [
        {
            "source_id": r["source_id"],
            "title": r["title"],
            "organization": r["organization"],
            "year": r["year"],
            "language": r["language"],
            "crop": r["crop"],
            "section": r["section"],
            "page": r["page"],
            "content_type": r["content_type"],
        }
        for r in records
    ]

    print(f"Loading {MODEL_NAME}...")
    model = RAGPretrainedModel.from_pretrained(MODEL_NAME)
    print(f"Indexing {len(collection)} Kinyarwanda chunks...")
    index_path = model.index(
        index_name=args.index_name,
        collection=collection,
        document_ids=document_ids,
        document_metadatas=metadatas,
    )
    print(f"Index built: {index_path}")


if __name__ == "__main__":
    main()
