"""A/B: heuristic leaf evaluator vs ValueNet leaf, both vs heuristic opponent.

Example:
  python -m perf.leaf_ab --games 40 --rollout-depth 0 --tag leaf_ab
  python -m perf.leaf_ab --games 80 --seed-start 100 --rollout-depth -1 --tag leaf_ab_depth3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcts import GameSpec, run_game
from mcts.consts import DEFAULT_ITERS, DEFAULT_ROLLOUT_DEPTH
from rollout import MovePolicyType
from value_net.infer import make_value_net_evaluator

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "value_net_sweeps"


def run_block(
    name: str,
    leaf_evaluator,
    seeds: range,
    iters: int,
    rollout_depth: int | None,
    max_search_seconds: float,
) -> dict:
    wins = timeouts = 0
    for seed in seeds:
        spec = GameSpec(
            seed=seed,
            mcts_seat=0,
            mcts_iters=iters,
            rollout_depth=rollout_depth,
            opponent_policy=MovePolicyType.HEURISTIC,
            leaf_evaluator=leaf_evaluator,
            max_search_seconds=max_search_seconds,
            max_game_seconds=90.0,
        )
        result = run_game(spec)
        if result.timed_out:
            timeouts += 1
        elif result.mcts_won:
            wins += 1
        print(
            f"[{name}] seed={seed} winner={result.winner} "
            f"timeout={result.timed_out} steps={result.steps}",
            flush=True,
        )
    played = len(seeds) - timeouts
    return {
        "name": name,
        "games": len(seeds),
        "wins": wins,
        "timeouts": timeouts,
        "win_rate": wins / max(played, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=40)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--iters", type=int, default=min(DEFAULT_ITERS, 100))
    parser.add_argument(
        "--rollout-depth",
        type=int,
        default=0,
        help="use -1 for DEFAULT_ROLLOUT_DEPTH",
    )
    parser.add_argument("--max-search-seconds", type=float, default=2.0)
    parser.add_argument("--tag", type=str, default="leaf_ab")
    args = parser.parse_args()

    if args.rollout_depth < 0:
        rollout_depth: int | None = DEFAULT_ROLLOUT_DEPTH
    else:
        rollout_depth = args.rollout_depth

    seeds = range(args.seed_start, args.seed_start + args.games)
    print(
        f"loading value net… games={args.games} iters={args.iters} "
        f"rollout_depth={rollout_depth}",
        flush=True,
    )
    net_eval = make_value_net_evaluator()
    results = [
        run_block(
            "heuristic_leaf",
            None,
            seeds,
            args.iters,
            rollout_depth,
            args.max_search_seconds,
        ),
        run_block(
            "value_net_leaf",
            net_eval,
            seeds,
            args.iters,
            rollout_depth,
            args.max_search_seconds,
        ),
    ]
    payload = {
        "iters": args.iters,
        "rollout_depth": rollout_depth,
        "seed_start": args.seed_start,
        "results": results,
    }
    out = OUT_DIR / f"{args.tag}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    print("\n=== leaf A/B ===", flush=True)
    for r in results:
        print(
            f"{r['name']}: {r['wins']}/{r['games'] - r['timeouts']} "
            f"(timeouts={r['timeouts']}) win_rate={r['win_rate']:.3f}",
            flush=True,
        )
    print(f"Wrote {out}", flush=True)


if __name__ == "__main__":
    main()
