from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from models.game.commands import GameCommand
from serialization.cards import serialize_card, serialize_property_set
from serialization.moves import move_to_dict
from serialization.state import serialize_pending

from .decision_row import DecisionRow

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
        {"move": move_to_dict(move), "visit_share": share}
        for move, share in ranked
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
