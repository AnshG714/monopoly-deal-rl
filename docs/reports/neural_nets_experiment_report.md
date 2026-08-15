# Neural Net Experiments (Value + Policy)

## Bottom Line

1. **Value net works as an MCTS leaf evaluator.** Against a heuristic opponent, swapping the handcrafted leaf score for the net raised win rate from **52.5% → 70%** (`rollout_depth=0`) and **66.3% → 72.5%** (default `rollout_depth=3`).
2. **Overfitting was a training issue, not a “need more games” issue.** More self-play data barely moved best val loss; smaller net + dropout + weight decay + lower LR fixed the train↓/val↑ blow-up.
3. **Policy net (move prior) also helps pruning.** With richer action features (v1), PolicyNet prune beat heuristic `score_move` prune **72.5% vs 60%** on a matched 40-game block (cap=5). This lines up with the earlier MCTS finding that **candidate pruning is the big lever**.

Checkpoints:

- `outputs/best_value_net.pth`
- `outputs/best_policy_net.pth`

---

## What We Can Act On

1. **Use the value net at MCTS leaves** via `GameSpec(leaf_evaluator=make_value_net_evaluator())` / `ISMCTSSolver(leaf_evaluator=...)`.
2. **Use the policy net for candidate pruning** via `GameSpec(move_prior=make_policy_move_prior())`.
3. **Keep training on all game steps** for the value net (late-game-only training predicts late states better but transfers worse to early states that MCTS still needs).
4. **Next scale-up:** train the policy net on the full self-play CSV (50k rows already materialized at `data/encoded/policy_50k.pt`), then a larger A/B; optional joint value+policy agent vs heuristic.

Companion report: [MCTS Experiment Report](mcts_experiment_report.md) (heuristic pruning / rollout depth).

---

## Pipeline

```text
self-play CSV  →  materialize tensors  →  train  →  hook into ISMCTS
     │                    │                 │
     │                    ├─ state features (value)
     │                    └─ state + action features (policy)
     └─ visits_json = policy training targets
```

| Step | Command |
| --- | --- |
| Encode states for value net | `python -m data.materialize.state data/self_play/data_10000_2500.csv` → `data/encoded/<stem>.pt` |
| Train value net | `python -m value_net.train` |
| Materialize policy examples | `python -m data.materialize.policy data/self_play/….csv [--limit N] [--tag NAME]` |
| Train policy net | `python -m policy_net.train --data data/encoded/smoke_policy.pt` |
| Leaf A/B | `python -m perf.leaf_ab --games 40 --rollout-depth 0` |
| Prior A/B | `python -m perf.prior_ab` |

Raw sweep JSON lives under `outputs/value_net_sweeps/` (gitignored-style experiment dumps; see individual files named in tables below).

---

## Value Net

### Problem

Training on CSV with ad-hoc encoding was slow. Once on the big encoded set (~765k rows), a `(128,64)` net at lr `1e-3` still **memorized**: train BCE → 0.28 while val → 1.24. Best val was essentially epoch 1.

### Fix (defaults in `value_net/`)

| Knob | Value |
| --- | --- |
| Hidden | `(64, 32)` |
| Dropout | `0.3` |
| Adam lr | `1e-4` |
| Weight decay | `1e-3` |
| Batch | `256` |
| Early stop | patience 5 on val BCE |
| Split | by game `seed` (80/20) |

Confirmed: best val BCE **0.5387**, train≈val (~0.53/0.54), val accuracy ≈ **72%** (constant baseline ≈ 51%).

### Regularization sweep (best val BCE)

| Config | Best val | Notes |
| --- | --- | --- |
| `lr_1e4_wd_drop` **(winner)** | **0.539** | train/val gap ~0.01 |
| `lr_3e4_wd` | 0.540 | |
| `small_64_32` | 0.540 | |
| `wd_1e2` | 0.558 | no overfit, weaker ceiling |
| baseline | 0.561 | then diverges hard |

Data scaling (same val games): more training games softened late overfitting but only moved best val **0.56 → 0.54**. **Regularization > more of the same data.**

One-off sweep / late-game scripts were removed; the tables in this report are the record.

### Late-game filter

| min_step | Train N | Acc (filtered) | Val loss on *all* steps |
| --- | --- | --- | --- |
| 0 | 611k | 71.6% | 0.540 |
| 60 | 152k | **76.0%** | **0.570** (worse transfer) |

Do **not** filter by step for the default leaf net.

### Leaf evaluator A/B vs heuristic opponent

| Config | Heuristic leaf | Value-net leaf |
| --- | --- | --- |
| 40 games, depth 0, seeds 0–39, 100 iters | 21/40 (**52.5%**) | 28/40 (**70.0%**) |
| 80 games, depth 3, seeds 100–179, 100 iters | 53/80 (**66.3%**) | 58/80 (**72.5%**) |

Artifacts: `leaf_ab.json`, `leaf_ab_depth3.json`.

---

## Policy Net

### Setup

- **Target:** MCTS `visit_share` over legal moves (KL to softmax).
- **Model:** `PolicyNet(state, action) → logit`, then softmax over the legal set.
- **v0 actions:** kind one-hot (`ACTION_DIM=18`).
- **v1 actions:** kind + move-scoring bucket + hand_index + color (`ACTION_DIM=37`).

Hook: `PolicyMovePrior` implements batched scoring for prune + per-move scores for expansion (`GameSpec.move_prior`).

### Prior A/B vs heuristic opponent (cap=5, depth 0)

| Prior | Games | Win rate |
| --- | --- | --- |
| Heuristic `score_move` | 40 (seeds 200–239) | **60%** |
| Policy v0 (kind only) | 40 | **65%** |
| Policy v1 (kind+bucket+color) | 40 | **72.5%** |
| Heuristic (20-game, iters 80) | 20 | 45% |
| Policy v1 (20-game, iters 80) | 20 | 60% |

Samples are still modest, but the direction is consistent: learned prior ≥ handcrafted prior, and v1 > v0.

Smoke train (2k decisions): best val KL ≈ **0.046**. Larger set materialized at `data/encoded/policy_50k.pt` (50k decisions); retrain with:

`python -m policy_net.train --data data/encoded/policy_50k.pt`

---

## Next Steps

1. `python -m policy_net.train --data data/encoded/policy_50k.pt` then re-run `python -m perf.prior_ab` at 40–80 games.
2. Combined agent: value leaf **and** policy prune vs heuristic (and vs value-only / policy-only).
3. Richer actions if needed (set-completion flag needs a live `Game`, not just CSV params).
4. Optional: larger leaf A/B (200+ games) for tighter confidence intervals.
