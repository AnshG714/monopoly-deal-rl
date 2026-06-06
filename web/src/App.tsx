import { useMemo, useState } from 'react'
import type { DragEvent } from 'react'

import { DeckGallery } from './components/DeckGallery'
import { LegalMoves } from './components/LegalMoves'
import { PlayerPanel } from './components/PlayerPanel'
import { StatusBar } from './components/StatusBar'
import { useGame } from './hooks/useGame'
import type { LegalMove } from './api/types'
import './App.css'

const PROPERTY_COLORS = [
  'brown',
  'light_blue',
  'pink',
  'orange',
  'red',
  'yellow',
  'green',
  'blue',
  'railroad',
  'utility',
]

function App() {
  const { game, loading, error, startGame, playMove } = useGame()
  const [seedInput, setSeedInput] = useState('')
  const [mctsInput, setMctsInput] = useState('')
  const [draggedHandIndex, setDraggedHandIndex] = useState<number | null>(null)
  const [interactionMessage, setInteractionMessage] = useState<string | null>(null)
  const isDeckRoute = window.location.pathname === '/deck'

  const handleStart = () => {
    const seed = seedInput.trim() ? Number(seedInput) : undefined
    const mcts_iterations = mctsInput.trim() ? Number(mctsInput) : undefined
    void startGame({ seed, mcts_iterations })
  }

  const isHumanTurn =
    game !== null &&
    !game.is_over &&
    game.acting_player_idx === game.viewer

  const isMainPhaseDragTurn =
    isHumanTurn && game?.state.pending === null && game.legal_moves.length > 0

  const viewer = game?.state.players.find((player) => player.idx === game.viewer)
  const opponent = game?.state.players.find((player) => player.idx !== game.viewer)

  const emptyPropertyColors = useMemo(() => {
    if (!viewer) return PROPERTY_COLORS
    const occupied = new Set(viewer.property_sets.map((set) => set.color))
    return PROPERTY_COLORS.filter((color) => !occupied.has(color))
  }, [viewer])

  const playMatchingMove = (candidates: LegalMove[], emptyMessage: string) => {
    if (!game) return
    if (candidates.length === 0) {
      setInteractionMessage(emptyMessage)
      return
    }
    if (candidates.length > 1) {
      setInteractionMessage(
        `That drop has ${candidates.length} legal interpretations. Use the move list for now.`,
      )
      return
    }
    setInteractionMessage(null)
    void playMove(candidates[0].id)
  }

  const withDraggedCard = (predicate: (move: LegalMove) => boolean) => {
    if (!game || draggedHandIndex === null) return []
    return game.legal_moves.filter(
      (move) => move.params.hand_index === draggedHandIndex && predicate(move),
    )
  }

  const handleDropToBank = () => {
    playMatchingMove(
      withDraggedCard((move) => move.kind === 'PlayMoneyFromHand'),
      'That card cannot be banked right now.',
    )
  }

  const handleDropToPlayArea = () => {
    playMatchingMove(
      withDraggedCard((move) =>
        ['PlayPassGo', 'PlayItsMyBirthday'].includes(move.kind),
      ),
      'Drop targeted actions onto the opponent or a property set.',
    )
  }

  const handleDropToOpponent = () => {
    if (!opponent) return
    playMatchingMove(
      withDraggedCard(
        (move) =>
          move.params.victim_idx === opponent.idx ||
          move.params.target_player_idx === opponent.idx,
      ),
      'That card does not have a simple opponent-target move right now.',
    )
  }

  const handleDropToPropertyColor = (color: string) => {
    playMatchingMove(
      withDraggedCard(
        (move) =>
          move.kind === 'PlayPropertyFromHand' &&
          move.params.into_color === color,
      ),
      `That card cannot be played into ${color.replaceAll('_', ' ')}.`,
    )
  }

  const handleDropToPropertySet = (setIdx: number, color: string) => {
    playMatchingMove(
      withDraggedCard(
        (move) =>
          (move.kind === 'PlayPropertyFromHand' &&
            move.params.into_color === color) ||
          (['PlayHouse', 'PlayHotel'].includes(move.kind) &&
            move.params.target_set_idx === setIdx),
      ),
      'That card cannot be played on this property set.',
    )
  }

  const allowDrop = (event: DragEvent<HTMLElement>) => {
    if (!isMainPhaseDragTurn) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Monopoly Deal</h1>
          <p className="app-header__subtitle">Play against MCTS AI</p>
        </div>

        <nav className="app-nav" aria-label="Primary">
          <a className={!isDeckRoute ? 'app-nav__link--active' : ''} href="/">
            Game
          </a>
          <a className={isDeckRoute ? 'app-nav__link--active' : ''} href="/deck">
            Deck
          </a>
        </nav>

        {!isDeckRoute && (
          <div className="new-game">
          <label>
            Seed
            <input
              type="number"
              value={seedInput}
              onChange={(e) => setSeedInput(e.target.value)}
              placeholder="random"
            />
          </label>
          <label>
            MCTS iters
            <input
              type="number"
              min={1}
              value={mctsInput}
              onChange={(e) => setMctsInput(e.target.value)}
              placeholder="500"
            />
          </label>
          <button type="button" onClick={handleStart} disabled={loading}>
            {game ? 'New game' : 'Start game'}
          </button>
          </div>
        )}
      </header>

      {isDeckRoute && <DeckGallery />}

      {!isDeckRoute && error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}

      {!isDeckRoute && interactionMessage && (
        <div className="banner banner--hint" role="status">
          {interactionMessage}
        </div>
      )}

      {!isDeckRoute && loading && (
        <div className="banner banner--loading" role="status">
          {game ? 'AI is thinking…' : 'Starting game…'}
        </div>
      )}

      {!isDeckRoute && !game && !loading && (
        <main className="welcome">
          <p>
            Start a game to play as Player 0. The API runs the AI automatically
            after each of your moves.
          </p>
        </main>
      )}

      {!isDeckRoute && game && (
        <>
          <StatusBar game={game} />

          <main className="table">
            {opponent && (
              <div
                className={`opponent-drop${
                  isMainPhaseDragTurn ? ' drop-zone' : ''
                }`}
                onDragOver={allowDrop}
                onDrop={(event) => {
                  event.preventDefault()
                  handleDropToOpponent()
                }}
              >
                <PlayerPanel
                  player={opponent}
                  isViewer={false}
                  isActing={opponent.idx === game.acting_player_idx}
                  isCurrentTurn={opponent.idx === game.current_player_idx}
                />
                {isMainPhaseDragTurn && (
                  <span className="drop-zone__label">
                    Drop rent or target actions here
                  </span>
                )}
              </div>
            )}

            <section className="center-playmat">
              <div
                className="play-target drop-zone"
                onDragOver={allowDrop}
                onDrop={(event) => {
                  event.preventDefault()
                  handleDropToPlayArea()
                }}
              >
                <h2>Play Area</h2>
                <p>Drop non-target actions here, like Pass Go or Birthday.</p>
              </div>

              <div
                className="play-target drop-zone"
                onDragOver={allowDrop}
                onDrop={(event) => {
                  event.preventDefault()
                  handleDropToBank()
                }}
              >
                <h2>Your Bank</h2>
                <p>Drop money or action/rent cards here to bank their value.</p>
              </div>
            </section>

            {viewer && (
              <section className="property-zones">
                <h2>Your Property Lots</h2>
                <div className="property-color-grid">
                  {emptyPropertyColors.map((color) => (
                    <button
                      key={color}
                      type="button"
                      className={`property-color-slot property-color-slot--${color}`}
                      onDragOver={allowDrop}
                      onDrop={(event) => {
                        event.preventDefault()
                        handleDropToPropertyColor(color)
                      }}
                    >
                      {color.replaceAll('_', ' ')}
                    </button>
                  ))}
                </div>
              </section>
            )}

            {viewer && (
              <PlayerPanel
                player={viewer}
                isViewer
                isActing={viewer.idx === game.acting_player_idx}
                isCurrentTurn={viewer.idx === game.current_player_idx}
                canDragHandCards={isMainPhaseDragTurn}
                canDropOnProperties={isMainPhaseDragTurn}
                onHandCardDragStart={(handIndex) => {
                  setDraggedHandIndex(handIndex)
                  setInteractionMessage(null)
                }}
                onDropOnPropertySet={handleDropToPropertySet}
              />
            )}
          </main>

          {isHumanTurn && game.state.pending !== null && (
            <LegalMoves
              moves={game.legal_moves}
              disabled={loading}
              onSelect={(moveId) => void playMove(moveId)}
            />
          )}

          {isHumanTurn && game.state.pending === null && (
            <details className="move-debug">
              <summary>Legal move list</summary>
              <LegalMoves
                moves={game.legal_moves}
                disabled={loading}
                onSelect={(moveId) => void playMove(moveId)}
              />
            </details>
          )}
        </>
      )}
    </div>
  )
}

export default App
