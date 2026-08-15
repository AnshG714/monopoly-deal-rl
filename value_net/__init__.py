"""Value network: win-probability from encoded game state."""

from .infer import make_value_net_evaluator
from .model import ValueNet

__all__ = ["ValueNet", "make_value_net_evaluator"]
