# Monopoly Deal API

Start the server:

```bash
uv run serve --reload
```

Docs: http://127.0.0.1:8000/docs

## Flow

1. **`POST /games`** — start a game. Optional body: `{ "seed": 42, "mcts_iterations": 500 }`.
2. **`GET /games/{game_id}`** — fetch current state (your hand + public board).
3. **`POST /games/{game_id}/moves`** — play `{ "move_id": N }` where `N` is the `id` from `legal_moves`.

After each move POST, the AI responds automatically until it is your turn again (or the game ends). The response always includes fresh `state` and `legal_moves` (empty when you are not acting).

Pick moves only by `move_id` from the latest `legal_moves` list — do not reconstruct moves from `params`.
