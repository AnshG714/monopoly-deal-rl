from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, cast

from models.game.commands import EndTurn, GameCommand
from models.player import BankableCard
from serialization.cards import (
    deserialize_card,
    deserialize_property_set,
    serialize_card,
    serialize_property_set,
)
from serialization.moves import move_to_dict
from serialization.state import deserialize_pending, serialize_pending

from .decision_row import DecisionRow

# Needed because we currently store big JSON blobs in the CSV file
csv.field_size_limit(sys.maxsize)

CSV_COLUMNS = (
    "seed",
    "step",
    "viewer_idx",
    "opponent_hand_size",
    "plays_this_turn",
    "timed_out",
    "viewer_won",
    "chosen_move_json",
    "legal_moves_json",
    "visits_json",
    "viewer_hand_json",
    "viewer_bank_json",
    "viewer_property_piles_json",
    "opponent_property_piles_json",
    "opponent_bank_json",
    "pending_json",
)


def _json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"))


def _visits_payload(visits: dict[GameCommand, float]) -> list[dict[str, Any]]:
    ranked = sorted(visits.items(), key=lambda item: item[1], reverse=True)
    return [
        {"move": move_to_dict(move), "visit_share": share} for move, share in ranked
    ]


def decision_row_to_csv_record(row: DecisionRow) -> dict[str, Any]:
    return {
        "seed": row.seed,
        "step": row.step,
        "viewer_idx": row.viewer_idx,
        "opponent_hand_size": row.opponent_hand_size,
        "plays_this_turn": row.plays_this_turn,
        "timed_out": row.timed_out,
        "viewer_won": row.viewer_won,
        "chosen_move_json": _json(move_to_dict(row.chosen_move)),
        "legal_moves_json": _json([move_to_dict(move) for move in row.legal_moves]),
        "visits_json": _json(_visits_payload(row.visits)),
        "viewer_hand_json": _json([serialize_card(card) for card in row.viewer_hand]),
        "viewer_bank_json": _json([serialize_card(card) for card in row.viewer_bank]),
        "viewer_property_piles_json": _json(
            [serialize_property_set(pile) for pile in row.viewer_property_piles]
        ),
        "opponent_property_piles_json": _json(
            [serialize_property_set(pile) for pile in row.opponent_property_piles]
        ),
        "opponent_bank_json": _json(
            [serialize_card(card) for card in row.opponent_bank]
        ),
        "pending_json": _json(serialize_pending(row.pending)),
    }


def write_decision_rows_csv(path: Path, rows: list[DecisionRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            record = decision_row_to_csv_record(row)
            writer.writerow({column: record[column] for column in CSV_COLUMNS})


def merge_decision_rows_csvs(sources: list[Path], destination: Path) -> int:
    """Concatenate chunk CSVs into one dataset. Returns total data rows written."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with destination.open("w", newline="", encoding="utf-8") as out_handle:
        writer: csv.DictWriter | None = None
        for source in sources:
            with source.open(newline="", encoding="utf-8") as in_handle:
                reader = csv.DictReader(in_handle)
                if writer is None:
                    writer = csv.DictWriter(out_handle, fieldnames=CSV_COLUMNS)
                    writer.writeheader()
                for record in reader:
                    writer.writerow({column: record[column] for column in CSV_COLUMNS})
                    row_count += 1
    return row_count


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes"}


def _parse_json_list(raw: str) -> list:
    if not raw:
        return []
    return json.loads(raw)


def csv_record_to_decision_row(record: dict[str, Any]) -> DecisionRow:
    """Rebuild a ``DecisionRow`` for encoding; move fields are placeholders."""
    pending_raw = record.get("pending_json") or "null"
    pending_payload = json.loads(pending_raw)

    return DecisionRow(
        seed=int(record["seed"]),
        step=int(record["step"]),
        viewer_idx=int(record["viewer_idx"]),
        chosen_move=EndTurn(),
        legal_moves=[],
        visits={},
        viewer_property_piles=[
            deserialize_property_set(payload)
            for payload in _parse_json_list(record["viewer_property_piles_json"])
        ],
        viewer_hand=[
            deserialize_card(payload)
            for payload in _parse_json_list(record["viewer_hand_json"])
        ],
        viewer_bank=cast(
            list[BankableCard],
            [deserialize_card(payload) for payload in _parse_json_list(record["viewer_bank_json"])],
        ),
        opponent_property_piles=[
            deserialize_property_set(payload)
            for payload in _parse_json_list(record["opponent_property_piles_json"])
        ],
        opponent_bank=cast(
            list[BankableCard],
            [
                deserialize_card(payload)
                for payload in _parse_json_list(record["opponent_bank_json"])
            ],
        ),
        opponent_hand_size=int(record["opponent_hand_size"]),
        plays_this_turn=int(record["plays_this_turn"]),
        pending=deserialize_pending(pending_payload),
        timed_out=_parse_bool(record["timed_out"]),
        viewer_won=_parse_bool(record["viewer_won"]),
    )


def read_decision_rows_csv(path: Path) -> list[DecisionRow]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [csv_record_to_decision_row(record) for record in csv.DictReader(handle)]
