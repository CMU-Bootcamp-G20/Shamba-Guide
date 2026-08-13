from __future__ import annotations

from typing import Protocol

from shambaguide.schemas import AdviceRequest, EvidenceChunk


class Retriever(Protocol):
    name: str

    def retrieve(self, request: AdviceRequest, *, top_k: int = 5) -> list[EvidenceChunk]:
        """Return reviewed, source-preserving evidence for one advisory request."""


class EmptyRetriever:
    """Safe development default used until the local hybrid index is connected."""

    name = "not-configured"

    def retrieve(self, request: AdviceRequest, *, top_k: int = 5) -> list[EvidenceChunk]:
        del request, top_k
        return []
