# Monopoly Deal Web UI

React client for playing against the MCTS AI via the [REST API](../api/README.md).

## Run locally

Terminal 1 — API (from repo root):

```bash
uv run serve --reload
```

Terminal 2 — frontend:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/games` to `http://127.0.0.1:8000`.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `""` (same origin) | API base URL for production builds |

## Project layout

```
src/
  api/          # fetch client + TypeScript types matching api/schemas.py
  components/   # board, hand, legal move buttons
  hooks/        # useGame — create game + apply moves
```

## What’s next (for you)

The scaffold is intentionally functional, not polished. Good next steps:

1. **Card art** — map `serialize_card` fields to real Monopoly Deal card images.
2. **Move UX** — group moves by kind; show `params` as pickers instead of a flat list.
3. **Pending interrupts** — highlight when `state.pending` is set (rent, steal, JSN).
4. **Persistence** — store `game_id` in `sessionStorage` so refresh doesn’t lose the game.
