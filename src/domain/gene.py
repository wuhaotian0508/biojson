from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class GeneBucket(StrEnum):
    COMMON = "Common_Genes"
    PATHWAY = "Pathway_Genes"
    REGULATION = "Regulation_Genes"
    PLANT = "Plant_Genes"


@dataclass(frozen=True)
class GeneRecord:
    bucket: GeneBucket
    name: str
    fields: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, *, bucket: GeneBucket, data: Mapping[str, Any]) -> "GeneRecord":
        fields = dict(data)
        return cls(
            bucket=bucket,
            name=str(fields.get("Gene_Name") or "Unknown"),
            fields=MappingProxyType(fields),
        )

    def field(self, name: str, default: Any = None) -> Any:
        return self.fields.get(name, default)
