"""A/B: heuristic move pruning vs PolicyNet prior pruning.

Example:
  python -m perf.prior_ab --games 40 --seed-start 200 --iters 100
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcts import GameSpec, HeuristicMovePrior, run_game
from mcts.consts import DEFAULT_ITERS
from policy_net import make_policy_move_prior
from rollout import MovePolicyType

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "value_net_sweeps"


def run_block(
    name: str,
    move_prior,
    seeds: range,
    iters: int,
    max_search_seconds: float,
    max_game_seconds: float,
) -> dict:
    wins = timeouts = 0
    for seed in seeds:
        spec = GameSpec(
            seed=seed,
            mcts_seat=0,
            mcts_iters=iters,
            rollout_depth=0,
            max_candidate_moves=5,
            opponent_policy=MovePolicyType.HEURISTIC,
            move_prior=move_prior,
            max_search_seconds=max_search_seconds,
            max_game_seconds=max_game_seconds,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=40)
    parser.add_argument("--seed-start", type=int, default=200)
    parser.add_argument("--iters", type=int, default=min(DEFAULT_ITERS, 100))
    parser.add_argument("--max-search-seconds", type=float, default=3.0)
    parser.add_argument("--max-game-seconds", type=float, default=120.0)
    parser.add_argument("--tag", type=str, default="policy_prior_ab")
    args = parser.parse_args()

    seeds = range(args.seed_start, args.seed_start + args.games)
    print(
        f"loading policy net… games={args.games} iters={args.iters}",
        flush=True,
    )
    policy_prior = make_policy_move_prior()
    results = [
        run_block(
            "heuristic_prior",
            HeuristicMovePrior(),
            seeds,
            args.iters,
            args.max_search_seconds,
            args.max_game_seconds,
        ),
        run_block(
            "policy_prior",
            policy_prior,
            seeds,
            args.iters,
            args.max_search_seconds,
            args.max_game_seconds,
        ),
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.tag}.json"
    out.write_text(
        json.dumps(
            {
                "iters": args.iters,
                "rollout_depth": 0,
                "max_candidate_moves": 5,
                "seed_start": args.seed_start,
                "results": results,
            },
            indent=2,
        )
    )
    print("\n=== policy prior A/B ===", flush=True)
    for row in results:
        print(
            f"{row['name']}: {row['wins']}/{row['games'] - row['timeouts']} "
            f"(timeouts={row['timeouts']}) win_rate={row['win_rate']:.3f}",
            flush=True,
        )
    print(f"Wrote {out}", flush=True)


if __name__ == "__main__":
    main()
