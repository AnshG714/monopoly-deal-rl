from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import Dataset

from data.csv_io import read_decision_rows_csv
from data.encoder import encode_decision_row, STATE_DIM


@dataclass(frozen=True)
class Example:
    seed: int
    features: list[float]  # length STATE_DIM
    label: float  # 0.0 oe


def load_examples(csv_path: Path) -> list[Example]:
    rows = read_decision_rows_csv(csv_path)
    examples = []
    for row in rows:
        if row.timed_out:
            continue

        examples.append(
            Example(
                seed=row.seed,
                features=encode_decision_row(row),
                label=1.0 if row.viewer_won else 0.0,
            )
        )

    return examples


def split_by_seed(examples: list[Example], val_fraction: float = 0.2):
    seeds = sorted({ex.seed for ex in examples})
    n_val = max(1, int(len(seeds) * val_fraction))
    val_seeds = set(seeds[-n_val:])
    train = [ex for ex in examples if ex.seed not in val_seeds]
    val = [ex for ex in examples if ex.seed in val_seeds]
    return train, val


class DecisionRowDataset(Dataset):
    def __init__(self, examples: list[Example]):
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        ex = self.examples[idx]
        x = torch.tensor(ex.features, dtype=torch.float32)
        y = torch.tensor(ex.label, dtype=torch.float32)
        return x, y
