from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from domain.gene import GeneBucket, GeneRecord


@dataclass(frozen=True)
class PaperRecord:
    title: str
    journal: str
    doi: str
    genes: tuple[GeneRecord, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PaperRecord":
        genes: list[GeneRecord] = []
        for bucket in GeneBucket:
            for gene_data in data.get(bucket.value) or []:
                genes.append(GeneRecord.from_mapping(bucket=bucket, data=gene_data))

        metadata = {
            key: value
            for key, value in data.items()
            if key not in {bucket.value for bucket in GeneBucket}
        }
        return cls(
            title=str(data.get("Title") or "Unknown"),
            journal=str(data.get("Journal") or "Unknown"),
            doi=str(data.get("DOI") or "Unknown"),
            genes=tuple(genes),
            metadata=MappingProxyType(dict(metadata)),
        )
