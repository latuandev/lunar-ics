"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_file(path: Path, payload: Any) -> None:
    """Write UTF-8 JSON with deterministic formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def read_json_file(path: Path) -> Any:
    """Read a UTF-8 JSON document."""

    return json.loads(path.read_text(encoding="utf-8"))

