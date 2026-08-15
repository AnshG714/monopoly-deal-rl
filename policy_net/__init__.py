"""Policy network: score legal moves from (state, action) features.

Trains on MCTS visit shares from self-play. Wire into search via
``GameSpec(move_prior=make_policy_move_prior())``.

See ``docs/reports/neural_nets_experiment_report.md``.
"""

from .model import PolicyNet
from .prior import PolicyMovePrior, make_policy_move_prior

__all__ = [
    "PolicyMovePrior",
    "PolicyNet",
    "make_policy_move_prior",
]
