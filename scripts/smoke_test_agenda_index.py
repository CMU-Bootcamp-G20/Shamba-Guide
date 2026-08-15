import argparse
import warnings
import torch
import transformers

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
torch.set_default_device("cpu")
transformers.AdamW = torch.optim.AdamW

from ragatouille import RAGPretrainedModel


DEFAULT_QUERIES = [
    "Kubungabunga ubutaka no kurwanya isuri bikorwa bite?",
    "Ni gute nakwirinda isuri iterwa n'imvura?",
    "Ibigori birwaye Cyumya cyangwa Kirabiranya bigaragaza ibimenyetso ki?",
    "Ni gute nakwirinda Kirabiranya y'ibigori?",
    "Nkongwa yangiza ibigori ite kandi nayirwanya nte?",
    "Indwara n'ibyonnyi by'ibishyimbo ni ibihe?",
    "Akaribata cyangwa Nyiragakecuru y'ibishyimbo igaragaza ibimenyetso ki?",
    "Ibirayi bikunda ubutaka bumeze gute?",
    "Ikivejuru cy'umuceri ni iki kandi kigira ibimenyetso ki?",
    "Ni gute imyumbati ifatwa neza mu murima?",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--index",
        default=".ragatouille/colbert/indexes/shambaguide_kinya_agenda_2023",
    )
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    rag = RAGPretrainedModel.from_index(args.index)

    for q in DEFAULT_QUERIES:
        print("\nQUERY:", q)
        results = rag.search(q, k=args.top_k)

        for rank, result in enumerate(results, 1):
            md = result.get("document_metadata", {})
            print(
                f"  {rank}. score={float(result['score']):.3f} "
                f"id={result.get('document_id')} "
                f"crop={md.get('crop')} "
                f"page={md.get('page')} "
                f"section={md.get('section')}"
            )
            print(
                "     ",
                result["content"][:300].replace("\n", " "),
            )


if __name__ == "__main__":
    main()