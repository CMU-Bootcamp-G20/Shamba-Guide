from __future__ import annotations

import types
import warnings
from pathlib import Path
from typing import Protocol

import torch
import transformers
from ragatouille import RAGPretrainedModel
from shambaguide.schemas import AdviceRequest, EvidenceChunk

# Suppress standard PyTorch
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
torch.set_default_device("cpu")
transformers.AdamW = torch.optim.AdamW

import torch.utils.cpp_extension

def mock_cpp_extension_load(name, *args, **kwargs):
    mod = types.ModuleType(name)
    
    if name == "segmented_lookup_cpp":
        def _segmented_lookup(tensor, pids, lengths, offsets):
            pieces = [tensor[offsets[p]:offsets[p]+lengths[p]] for p in pids.tolist()]
            if not pieces:
                return torch.empty((0, tensor.size(-1)), dtype=tensor.dtype, device=tensor.device)
            return torch.cat(pieces, dim=0)
        mod.segmented_lookup = _segmented_lookup
        
    elif name == "filter_pids_cpp":
        def _filter_pids(pids, centroid_scores, max_pids):
            return pids[:max_pids], centroid_scores[:max_pids]
        mod.filter_pids = _filter_pids
        
    elif name == "segmented_maxsim_cpp":
        def _segmented_maxsim(*args, **kwargs):
            return None
        mod.segmented_maxsim = _segmented_maxsim
        
    return mod
class Retriever(Protocol):
    name: str

    def retrieve(
        self, request: AdviceRequest, *, top_k: int = 5
    ) -> list[EvidenceChunk]:
        """Return reviewed, source-preserving evidence for one advisory request."""

class EmptyRetriever:
    """Safe development default used until the local hybrid index is connected."""
    name = "not-configured"
    def retrieve(
        self, request: AdviceRequest, *, top_k: int = 5
    ) -> list[EvidenceChunk]:
        del request, top_k
        return []

class KinyaColBERTRetriever:
    """Live ColBERT semantic retriever using the C4IR-RW model."""
    name = "kinya-colbert-free"
    def __init__(
        self,
        index_path: str | Path = ".ragatouille/colbert/indexes/shambaguide_kinya",
        min_score: float = 12.0,
    ):
        self.index_path = str(index_path)
        self.min_score = min_score

        # Load the pre-built FAISS index from disk
        self._rag = RAGPretrainedModel.from_index(self.index_path)

    def retrieve(
        self, request: AdviceRequest, *, top_k: int = 5
    ) -> list[EvidenceChunk]:
        raw_results = self._rag.search(request.question, k=top_k)
        evidence: list[EvidenceChunk] = []

        for result in raw_results:
            score = float(result["score"])

            # Gate 1: Retrieval Relevance Threshold
            if score < self.min_score:
                continue

            metadata = result.get("document_metadata", {})
            evidence.append(
                EvidenceChunk(
                    source_id=str(
                        result.get("document_id", f"doc-{result['passage_id']}")
                    ),
                    title=metadata.get("title", "RAB Agricultural Guidance"),
                    page=metadata.get("page"),
                    section=metadata.get("section"),
                    text=result["content"],
                    score=score,
                )
            )

        return evidence