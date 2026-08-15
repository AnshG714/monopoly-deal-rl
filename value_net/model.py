import torch
import torch.nn as nn
from typing import List

from data.encoder import STATE_DIM


class ValueNet(nn.Module):
    def __init__(
        self,
        input_dim: int = STATE_DIM,
        hidden: tuple[int, ...] = (64, 32),
        dropout: float = 0.3,
    ):
        super().__init__()
        layers: List[nn.Module] = []
        prev_dim = input_dim
        for width in hidden:
            layers.append(nn.Linear(prev_dim, width))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev_dim = width

        layers.append(nn.Linear(prev_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)
