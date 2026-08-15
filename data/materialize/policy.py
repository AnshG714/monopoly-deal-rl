"""Materialize policy-net examples from a self-play CSV.

Each example:
  state: Float[STATE_DIM]
  actions: Float[K, ACTION_DIM]
  target: Float[K]  # visit_share, renormalized
  seed / step

Usage:
  python -m data.materialize.policy data/self_play/….csv [--limit N] [--tag NAME]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from data.encoder import (
    ACTION_DIM,
    STATE_DIM,
    encode_action_payload,
    encode_decision_row,
)
from data.materialize.common import (
    default_output_path,
    materialize_examples,
    resolve_input_csv,
)


def materialize_policy(
    csv_path: Path,
    output_path: Path,
    *,
    limit: int | None = None,
) -> int:
    def build(record, row):
        visits = json.loads(record.get("visits_json") or "[]")
        if not visits:
            return None
        actions: list[list[float]] = []
        shares: list[float] = []
        for item in visits:
            share = float(item["visit_share"])
            actions.append(encode_action_payload(item["move"]))
            shares.append(share)
        total = sum(shares)
        if total <= 0:
            return None
        target = [share / total for share in shares]
        return {
            "state": torch.tensor(encode_decision_row(row), dtype=torch.float32),
            "actions": torch.tensor(actions, dtype=torch.float32),
            "target": torch.tensor(target, dtype=torch.float32),
            "seed": int(row.seed),
            "step": int(row.step),
        }

    examples, skipped = materialize_examples(csv_path, build, limit=limit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "examples": examples,
            "state_dim": STATE_DIM,
            "action_dim": ACTION_DIM,
            "n": len(examples),
            "skipped": skipped,
        },
        output_path,
    )
    return len(examples)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize policy-net tensors from a self-play CSV"
    )
    parser.add_argument("input", type=Path, help="self-play decision-row CSV")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="output stem (default: <csv_stem>_policy)",
    )
    args = parser.parse_args()

    csv_path = resolve_input_csv(args.input)
    stem = args.tag or f"{csv_path.stem}_policy"
    output_path = default_output_path(stem)
    n = materialize_policy(csv_path, output_path, limit=args.limit)
    print(f"Encoded {n} policy decisions -> {output_path}", flush=True)


if __name__ == "__main__":
    main()
