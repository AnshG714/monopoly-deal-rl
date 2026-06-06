import type { LegalMove } from '../api/types'

interface LegalMovesProps {
  moves: LegalMove[]
  disabled: boolean
  onSelect: (moveId: number) => void
}

export function LegalMoves({ moves, disabled, onSelect }: LegalMovesProps) {
  if (moves.length === 0) {
    return (
      <section className="legal-moves">
        <h2>Your moves</h2>
        <p className="muted">No legal moves — wait for the AI or start a new game.</p>
      </section>
    )
  }

  return (
    <section className="legal-moves">
      <h2>Your moves ({moves.length})</h2>
      <p className="legal-moves__hint">
        Pick a move by id from the server — labels are for display only.
      </p>
      <ul className="legal-moves__list">
        {moves.map((move) => (
          <li key={move.id}>
            <button
              type="button"
              className="move-button"
              disabled={disabled}
              onClick={() => onSelect(move.id)}
            >
              <span className="move-button__id">#{move.id}</span>
              <span className="move-button__label">{move.label}</span>
              <span className="move-button__kind">{move.kind}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
