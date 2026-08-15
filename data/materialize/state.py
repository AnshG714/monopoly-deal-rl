"""Materialize value-net state tensors from a self-play CSV.

Usage:
  python -m data.materialize.state data/self_play/data_10000_2500.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from data.encoder import STATE_DIM, encode_decision_row
from data.materialize.common import (
    default_output_path,
    materialize_examples,
    resolve_input_csv,
)


def materialize_state(csv_path: Path, output_path: Path) -> int:
    def build(_record, row):
        return {
            "features": encode_decision_row(row),
            "label": 1.0 if row.viewer_won else 0.0,
            "seed": row.seed,
            "step": row.step,
        }

    examples, _skipped = materialize_examples(csv_path, build)
    features = [ex["features"] for ex in examples]
    labels = [ex["label"] for ex in examples]
    seeds = [ex["seed"] for ex in examples]
    steps = [ex["step"] for ex in examples]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "features": torch.tensor(features, dtype=torch.float32),
            "labels": torch.tensor(labels, dtype=torch.float32),
            "seeds": torch.tensor(seeds, dtype=torch.long),
            "steps": torch.tensor(steps, dtype=torch.long),
            "state_dim": STATE_DIM,
        },
        output_path,
    )
    return len(examples)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize value-net state tensors from a self-play CSV"
    )
    parser.add_argument("input", type=Path, help="self-play decision-row CSV")
    args = parser.parse_args()

    csv_path = resolve_input_csv(args.input)
    output_path = default_output_path(csv_path.stem)
    n = materialize_state(csv_path, output_path)
    print(f"Encoded {n} rows -> {output_path}", flush=True)


if __name__ == "__main__":
    main()
