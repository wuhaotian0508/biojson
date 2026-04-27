from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from domain import PaperRecord


class VerifiedGeneRepository:
    """Repository for verified NutriMaster gene JSON files."""

    def __init__(
        self,
        data_dir: Path,
        *,
        file_pattern: str = "*_nutri_plant_verified.json",
    ):
        self.data_dir = Path(data_dir)
        self.file_pattern = file_pattern

    def iter_paths(self) -> Iterator[Path]:
        yield from sorted(self.data_dir.glob(self.file_pattern))

    def iter_papers(self) -> Iterator[PaperRecord]:
        for path in self.iter_paths():
            yield self.load_paper(path)

    def load_paper(self, path: Path) -> PaperRecord:
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
        return PaperRecord.from_mapping(data)
