from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from reference_harvester.models import ensure_parent


def write_jsonl(path: Path, records: Iterable[Mapping[str, object]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


__all__ = ["write_jsonl"]
