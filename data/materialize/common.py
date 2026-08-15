"""Shared CSV → tensor materialization helpers."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from data.csv_io import csv_record_to_decision_row
from data.decision_row import DecisionRow

# Needed because we currently store big JSON blobs in the CSV file
csv.field_size_limit(sys.maxsize)

ENCODED_DIR = Path(__file__).resolve().parent.parent / "encoded"

RowBuilder = Callable[[dict[str, str], DecisionRow], dict[str, Any] | None]


def materialize_examples(
    csv_path: Path,
    build_example: RowBuilder,
    *,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Walk a self-play CSV and build examples via ``build_example``.

    ``build_example(record, row)`` returns a dict to keep, or ``None`` to skip.
    Returns ``(examples, skipped_count)``.
    """
    examples: list[dict[str, Any]] = []
    skipped = 0
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            if limit is not None and len(examples) >= limit:
                break
            row = csv_record_to_decision_row(record)
            if row.timed_out:
                skipped += 1
                continue
            example = build_example(record, row)
            if example is None:
                skipped += 1
                continue
            examples.append(example)
    return examples, skipped


def resolve_input_csv(path: Path) -> Path:
    csv_path = path.expanduser().resolve()
    if not csv_path.is_file():
        raise SystemExit(f"input file does not exist: {csv_path}")
    return csv_path


def default_output_path(stem: str) -> Path:
    return ENCODED_DIR / f"{stem}.pt"
