"""Pairwise state+action scorer for legal-move priors."""

from __future__ import annotations

from typing import List

import torch
import torch.nn as nn

from data.encoder import ACTION_DIM, STATE_DIM


class PolicyNet(nn.Module):
    """Score one (state, action) pair; softmax over legal actions at inference."""

    def __init__(
        self,
        state_dim: int = STATE_DIM,
        action_dim: int = ACTION_DIM,
        hidden: tuple[int, ...] = (128, 64),
        dropout: float = 0.3,
    ):
        super().__init__()
        layers: List[nn.Module] = []
        prev = state_dim + action_dim
        for width in hidden:
            layers.append(nn.Linear(prev, width))
            layers.append(nn.ReLU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
            prev = width
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """
        Args:
            state: [B, STATE_DIM] or [B, K, STATE_DIM] (broadcastable with action)
            action: [B, ACTION_DIM] or [B, K, ACTION_DIM]
        Returns:
            logits: [B] or [B, K]
        """
        x = torch.cat([state, action], dim=-1)
        return self.net(x).squeeze(-1)
