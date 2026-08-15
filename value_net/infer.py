"""Inference helpers: Game state → ValueNet win probability."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import torch

from data.decision_row import game_to_decision_row
from data.encoder import encode_decision_row
from models.game.game import Game
from value_net.model import ValueNet

LeafEvaluator = Callable[[Game, int], float]

DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parent.parent / "outputs" / "best_value_net.pth"
)


def load_value_net(
    checkpoint: Path | None = None,
    device: torch.device | None = None,
) -> tuple[ValueNet, torch.device]:
    if device is None:
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
    path = checkpoint or DEFAULT_CHECKPOINT
    model = ValueNet()
    state = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, device


def make_value_net_evaluator(
    model: ValueNet | None = None,
    device: torch.device | None = None,
    checkpoint: Path | None = None,
) -> LeafEvaluator:
    """Return a leaf evaluator compatible with ``ISMCTSSolver``."""
    if model is None:
        model, device = load_value_net(checkpoint=checkpoint, device=device)
    elif device is None:
        device = next(model.parameters()).device

    @torch.no_grad()
    def evaluate(game: Game, player_idx: int) -> float:
        winner = game.winner_idx()
        if winner is not None:
            return 1.0 if winner == player_idx else 0.0
        features = encode_decision_row(game_to_decision_row(game, player_idx))
        x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
        return float(torch.sigmoid(model(x)).item())

    return evaluate
