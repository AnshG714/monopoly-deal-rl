from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import Dataset

from data.encoder import STATE_DIM


@dataclass(frozen=True)
class EncodedData:
    features: torch.Tensor  # [N, STATE_DIM]
    labels: torch.Tensor  # [N]
    seeds: torch.Tensor  # [N]
    steps: torch.Tensor | None = None  # [N], optional


def _slice(data: EncodedData, mask: torch.Tensor) -> EncodedData:
    return EncodedData(
        features=data.features[mask],
        labels=data.labels[mask],
        seeds=data.seeds[mask],
        steps=None if data.steps is None else data.steps[mask],
    )


def load_encoded(path: Path) -> EncodedData:
    payload = torch.load(path, weights_only=True)
    state_dim = int(payload["state_dim"])
    if state_dim != STATE_DIM:
        raise ValueError(
            f"encoded state_dim={state_dim} does not match encoder STATE_DIM={STATE_DIM}"
        )
    return EncodedData(
        features=payload["features"],
        labels=payload["labels"],
        seeds=payload["seeds"],
        steps=payload.get("steps"),
    )


def split_by_seed(
    data: EncodedData, val_fraction: float = 0.2
) -> tuple[EncodedData, EncodedData]:
    unique_seeds = sorted({int(seed) for seed in data.seeds.tolist()})
    n_val = max(1, int(len(unique_seeds) * val_fraction))
    val_seed_set = set(unique_seeds[-n_val:])
    val_mask = torch.tensor(
        [int(seed) in val_seed_set for seed in data.seeds.tolist()],
        dtype=torch.bool,
    )
    return _slice(data, ~val_mask), _slice(data, val_mask)


class EncodedDataset(Dataset):
    def __init__(self, data: EncodedData):
        self.features = data.features
        self.labels = data.labels

    def __len__(self) -> int:
        return self.features.size(0)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.labels[idx]
