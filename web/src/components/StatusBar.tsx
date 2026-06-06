import type { GameStateResponse } from '../api/types'

interface StatusBarProps {
  game: GameStateResponse
}

export function StatusBar({ game }: StatusBarProps) {
  const { state } = game
  const pending = state.pending

  return (
    <header className="status-bar">
      <div className="status-bar__meta">
        <span>Game {game.game_id.slice(0, 8)}…</span>
        {game.seed !== undefined && <span>Seed {game.seed}</span>}
        <span>Deck {state.deck_size}</span>
        <span>Discard {state.discard_size}</span>
        <span>Plays this turn {state.plays_this_turn}/3</span>
      </div>

      {pending && (
        <div className="status-bar__pending" role="status">
          Pending: <strong>{pending.kind}</strong>
        </div>
      )}

      {game.is_over && (
        <div className="status-bar__over" role="status">
          Game over —{' '}
          {game.winner_idx === game.viewer
            ? 'You win!'
            : `Player ${game.winner_idx} wins.`}
        </div>
      )}
    </header>
  )
}
