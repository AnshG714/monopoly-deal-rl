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

## Interaction model

The game table uses **desktop drag-and-drop** with **click fallbacks** (select a card, then click a highlighted target). Touch/mobile pointer drag is **not** supported in this pass.

Gestures are matched client-side against `legal_moves` params; moves are still submitted via `POST /games/{id}/moves` with `move_id`.

## Project layout

```
src/
  api/              # fetch client + TypeScript types
  components/
    game/           # GameScreen, GameTable, piles, panels
  game/             # moveMatchers, interactionTypes, useGameActions
  hooks/            # useGame
  styles/           # tokens.css
  utils/            # cn helper
```

## Tests

```bash
cd web
npm test
```
