"""Interactive helpers for stepping through IS-MCTS.

Run from the repo root:

    python -m mcts.debug snapshot
    python -m mcts.debug determinize --seed 42
    python -m mcts.debug step --seed 42 --iterations 3
    python -m mcts.debug search --seed 42 --iterations 100
    python -m mcts.debug rollout --seed 42
"""

from __future__ import annotations

import argparse
import random
import secrets
import traceback

from models.game.commands import GameCommand
from models.game.game import Game
from mcts.determinize import determinize
from mcts.node import ISMCTSNode
from mcts.solver import ISMCTSSolver
from rollout import rollout


def _move_label(game: Game, move: GameCommand) -> str:
    acting = game.players[game.acting_player_idx].name
    turn = game.players[game.current_player_idx].name
    name = type(move).__name__
    if acting != turn:
        return f"{name} ({acting} responds)"
    return name


def _hand_summary(game: Game, player_idx: int) -> str:
    hand = game.players[player_idx].hand
    cards = ", ".join(f"{c.type.value}:{c.value}M" for c in hand) or "(empty)"
    return f"{len(hand)} cards [{cards}]"


def print_snapshot(game: Game, *, title: str = "Game snapshot") -> None:
    """Print the fields that usually matter while debugging search."""
    print(f"=== {title} ===")
    print(f"current_player={game.players[game.current_player_idx].name}")
    print(f"acting_player={game.players[game.acting_player_idx].name}")
    print(f"pending={type(game.pending).__name__ if game.pending else None}")
    print(f"plays_this_turn={game.plays_this_turn}")
    print(f"deck={len(game.deck)}  discard={len(game.discard_pile)}")
    for i, player in enumerate(game.players):
        print(
            f"  {player.name}: sets={player.complete_set_count()}  "
            f"bank={len(player.money_pile)}  hand={_hand_summary(game, i)}"
        )

    moves = game.legal_moves()
    print(f"legal_moves ({len(moves)}):")
    for i, move in enumerate(moves):
        print(f"  [{i}] {_move_label(game, move)}  {move!r}")
    print(f"is_over={game.is_over()}  winner={game.winner_idx()}")
    print()


def print_root_stats(root: ISMCTSNode, *, root_player_idx: int) -> None:
    """Print visit/win stats for each child of the search root."""
    if not root.children:
        print("Root has no children yet.")
        return

    print("=== Root child stats ===")
    for child in sorted(root.children, key=lambda node: node.visits, reverse=True):
        move = child.move
        win_rate = child.wins / child.visits if child.visits else 0.0
        print(
            f"  {type(move).__name__!s:24}  "
            f"visits={child.visits:5d}  wins={child.wins:5d}  "
            f"rate={win_rate:.3f}  move={move!r}"
        )
    best = root.best_child()
    print(
        f"\nMost visited: {type(best.move).__name__} "
        f"(visits={best.visits}, wins={best.wins}, root_player={root_player_idx})"
    )
    print()


def trace_iteration(
    game: Game,
    root_node: ISMCTSNode,
    *,
    iteration: int,
    root_player_idx: int,
) -> tuple[int, ISMCTSNode]:
    """Run one IS-MCTS iteration with verbose logging.

    Mirrors ``ISMCTSSolver.search`` so you can see exactly where it stops or crashes.
    Returns ``(reward, leaf_node)``.
    """
    print(f"--- iteration {iteration} ---")
    determinized_game = determinize(game)
    node = root_node
    depth = 0

    print("After determinize:")
    print(
        f"  opponent hand size={len(determinized_game.players[1 - root_player_idx].hand)}  "
        f"deck={len(determinized_game.deck)}"
    )

    unexpanded_moves = node.get_unexpanded_moves(determinized_game.legal_moves())
    print(
        f"At depth {depth}: legal={len(determinized_game.legal_moves())}  "
        f"unexpanded={len(unexpanded_moves)}  children={len(node.children)}"
    )

    while not determinized_game.is_over():
        if unexpanded_moves:
            print(f"  stop selection at depth {depth}: node has unexpanded moves")
            break

        legal_moves = determinized_game.legal_moves()
        child = node.choose_child_uct(legal_moves)
        if child is None:
            print(
                f"  stop selection at depth {depth}: no legal UCT child "
                f"(legal_moves={len(legal_moves)}, children={len(node.children)})"
            )
            break

        print(
            f"  descend depth {depth} -> {depth + 1}: "
            f"{_move_label(determinized_game, child.move)}  {child.move!r}"
        )
        determinized_game.apply(child.move)
        node = child
        depth += 1
        unexpanded_moves = node.get_unexpanded_moves(determinized_game.legal_moves())
        print(
            f"At depth {depth}: acting={game.players[determinized_game.acting_player_idx].name}  "
            f"legal={len(determinized_game.legal_moves())}  "
            f"unexpanded={len(unexpanded_moves)}  children={len(node.children)}"
        )

    expanded = False
    if not determinized_game.is_over() and unexpanded_moves:
        move = game._rng.choice(unexpanded_moves)
        new_node = ISMCTSNode(move, node)
        node.children.append(new_node)
        node = new_node
        expanded = True
        print(f"Expanded: {_move_label(determinized_game, move)}  {move!r}")
        print(
            "NOTE: determinized_game has NOT been apply()'d with the expansion move yet."
        )
    elif determinized_game.is_over():
        print("Terminal state reached during selection/expansion.")
    else:
        print("No expansion this iteration (no unexpanded moves at leaf).")

    print(f"Rollout starting state: is_over={determinized_game.is_over()}")
    simulation_result = rollout(determinized_game)
    reward = 1 if simulation_result["winner"] == root_player_idx else 0
    print(
        f"Rollout finished: steps={simulation_result['steps']}  "
        f"winner={simulation_result['winner']}  reward={reward}"
    )

    node.backpropagate(reward)
    print(f"Backpropagated reward={reward} from leaf visits={node.visits}")
    if expanded:
        print(f"Expanded node now: visits={node.visits}, wins={node.wins}")
    print()
    return reward, node


def cmd_snapshot(args: argparse.Namespace) -> int:
    game = _game_from_args(args)
    print_snapshot(game)
    return 0


def cmd_determinize(args: argparse.Namespace) -> int:
    game = _game_from_args(args)
    print_snapshot(game, title="Before determinize")
    sample = determinize(game)
    print_snapshot(sample, title="After determinize")
    return 0


def cmd_step(args: argparse.Namespace) -> int:
    game = _game_from_args(args)
    root_player_idx = game.acting_player_idx
    root_node = ISMCTSNode()

    print_snapshot(game, title="Search root")
    for i in range(1, args.iterations + 1):
        try:
            trace_iteration(
                game,
                root_node,
                iteration=i,
                root_player_idx=root_player_idx,
            )
        except Exception:
            print("Iteration failed:")
            traceback.print_exc()
            return 1

    print_root_stats(root_node, root_player_idx=root_player_idx)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    game = _game_from_args(args)
    root_player_idx = game.acting_player_idx
    print_snapshot(game, title="Search root")

    solver = ISMCTSSolver(iterations=args.iterations)
    try:
        move = solver.search(game)
    except Exception:
        print("Search failed:")
        traceback.print_exc()
        return 1

    print(f"Chosen move: {_move_label(game, move)}  {move!r}")
    return 0


def cmd_rollout(args: argparse.Namespace) -> int:
    game = _game_from_args(args)
    print_snapshot(game, title="Rollout start")

    if args.determinize:
        game = determinize(game)
        print_snapshot(game, title="Determinized rollout start")

    result = rollout(game, max_steps=args.max_steps)
    print(
        f"Rollout finished: steps={result['steps']}  "
        f"winner={result['winner']} ({game.players[result['winner']].name})"
    )
    return 0


def _game_from_args(args: argparse.Namespace) -> Game:
    seed = args.seed if args.seed is not None else secrets.randbelow(2**31)
    game = Game(rng=random.Random(seed))
    game.start_match()
    print(f"seed={seed}\n")
    return game


def _add_seed_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=None,
        help="RNG seed (default: random)",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Debug IS-MCTS building blocks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser(
        "snapshot", help="print current game state and legal moves"
    )
    _add_seed_arg(snapshot_parser)

    determinize_parser = subparsers.add_parser(
        "determinize", help="print game state before/after one determinization"
    )
    _add_seed_arg(determinize_parser)

    step_parser = subparsers.add_parser(
        "step", help="trace individual MCTS iterations verbosely"
    )
    _add_seed_arg(step_parser)
    step_parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=1,
        help="how many traced iterations to run (default: 1)",
    )

    search_parser = subparsers.add_parser(
        "search", help="run ISMCTSSolver.search and print the chosen move"
    )
    _add_seed_arg(search_parser)
    search_parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=100,
        help="MCTS iterations (default: 100)",
    )

    rollout_parser = subparsers.add_parser(
        "rollout", help="run one heuristic rollout from the opening state"
    )
    _add_seed_arg(rollout_parser)
    rollout_parser.add_argument(
        "--determinize",
        action="store_true",
        help="determinize once before rolling out",
    )
    rollout_parser.add_argument("--max-steps", "-m", type=int, default=10_000)

    args = parser.parse_args(argv)

    commands = {
        "snapshot": cmd_snapshot,
        "determinize": cmd_determinize,
        "step": cmd_step,
        "search": cmd_search,
        "rollout": cmd_rollout,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
