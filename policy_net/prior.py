"""PolicyNet-backed ``MovePrior`` for MCTS pruning + expansion."""

from __future__ import annotations

from pathlib import Path

import torch

from data.decision_row import game_to_decision_row
from data.encoder import encode_action, encode_decision_row
from models.game.commands import GameCommand
from models.game.game import Game
from policy_net.model import PolicyNet

DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parent.parent / "outputs" / "best_policy_net.pth"
)


def load_policy_net(
    checkpoint: Path | None = None,
    device: torch.device | None = None,
) -> tuple[PolicyNet, torch.device]:
    if device is None:
        if torch.backends.mps.is_available():
            device = torch.device("mps")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
    path = checkpoint or DEFAULT_CHECKPOINT
    model = PolicyNet()
    state = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model, device


class PolicyMovePrior:
    """Batched PolicyNet prior implementing the ``mcts.MovePrior`` protocol."""

    def __init__(self, model: PolicyNet, device: torch.device):
        self.model = model
        self.device = device

    @torch.no_grad()
    def score_moves(
        self, game: Game, moves: list[GameCommand], root_player_idx: int
    ) -> list[float]:
        if not moves:
            return []
        acting = game.acting_player_idx
        features = encode_decision_row(game_to_decision_row(game, acting))
        state = torch.tensor(features, dtype=torch.float32, device=self.device)
        actions = torch.tensor(
            [encode_action(move) for move in moves],
            dtype=torch.float32,
            device=self.device,
        )
        state_b = state.unsqueeze(0).expand(actions.size(0), -1)
        logits = self.model(state_b, actions)
        perspective = 1.0 if acting == root_player_idx else -1.0
        return (perspective * logits).detach().cpu().tolist()

    def score(self, game: Game, move: GameCommand, root_player_idx: int) -> float:
        return self.score_moves(game, [move], root_player_idx)[0]

    def select_candidates(
        self,
        game: Game,
        moves: list[GameCommand],
        *,
        root_player_idx: int,
        max_moves: int,
        heuristic_move: GameCommand,
    ) -> list[GameCommand]:
        prefer_high = game.acting_player_idx == root_player_idx
        scores = self.score_moves(game, moves, root_player_idx)
        ranked = sorted(
            zip(scores, range(len(moves)), moves),
            reverse=prefer_high,
            key=lambda item: (item[0], -item[1] if prefer_high else item[1]),
        )
        selected = [move for _, _, move in ranked[:max_moves]]
        if heuristic_move in moves and heuristic_move not in selected:
            selected[-1] = heuristic_move
        return selected


def make_policy_move_prior(
    model: PolicyNet | None = None,
    device: torch.device | None = None,
    checkpoint: Path | None = None,
) -> PolicyMovePrior:
    if model is None:
        model, device = load_policy_net(checkpoint=checkpoint, device=device)
    elif device is None:
        device = next(model.parameters()).device
    return PolicyMovePrior(model, device)
