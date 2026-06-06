import { useMemo, useState } from "react";

import type {
  Card as CardType,
  LegalMove,
  Player,
  PropertySet,
} from "./api/types";
import { Card } from "./components/card";
import { useGame } from "./hooks/useGame";
import "./App.css";

const MAX_PLAYS = 3;

function moneyTotal(cards: CardType[]) {
  return cards.reduce((total, card) => total + card.value, 0);
}

function labelColor(color: string) {
  return color.replaceAll("_", " ");
}

function moveHasHandIndex(move: LegalMove, handIndex: number) {
  return Number(move.params.hand_index) === handIndex;
}

function sortedAssetKey(key: string) {
  const parts = key.split(":");
  return parts.map((part) => Number(part)).join(":");
}

function selectedDebtTotal(player: Player, keys: Set<string>) {
  let total = 0;
  for (const key of keys) {
    const parts = key.split(":");
    if (parts[0] === "money") {
      total += player.bank[Number(parts[1])]?.value ?? 0;
    }
    if (parts[0] === "property") {
      total +=
        player.property_sets[Number(parts[1])]?.cards[Number(parts[2])]
          ?.value ?? 0;
    }
  }
  return total;
}

function selectedPayDebtMove(moves: LegalMove[], keys: Set<string>) {
  const money = [...keys]
    .filter((key) => key.startsWith("money:"))
    .map((key) => Number(key.split(":")[1]))
    .sort((a, b) => a - b);
  const props = [...keys]
    .filter((key) => key.startsWith("property:"))
    .map((key) => {
      const [, setIdx, cardIdx] = key.split(":");
      return [Number(setIdx), Number(cardIdx)];
    })
    .sort((a, b) =>
      sortedAssetKey(a.join(":")).localeCompare(sortedAssetKey(b.join(":"))),
    );

  return moves.find((move) => {
    if (move.kind !== "PayDebt") return false;
    const moveMoney = (
      (move.params.money_pile_indices as number[] | undefined) ?? []
    )
      .map(Number)
      .sort((a, b) => a - b);
    const moveProps = (
      (move.params.property_card_indices as [number, number][] | undefined) ??
      []
    )
      .map(([setIdx, cardIdx]) => [Number(setIdx), Number(cardIdx)])
      .sort((a, b) =>
        sortedAssetKey(a.join(":")).localeCompare(sortedAssetKey(b.join(":"))),
      );

    return (
      JSON.stringify(moveMoney) === JSON.stringify(money) &&
      JSON.stringify(moveProps) === JSON.stringify(props)
    );
  });
}

interface ModalState {
  title: string;
  moves?: LegalMove[];
  cards?: CardType[];
}

function MiniBank({
  cards,
  label = "Bank",
}: {
  cards: CardType[];
  label?: string;
}) {
  return (
    <div className="bank">
      <div className="bank__label">
        <span>{label}</span>
        <strong>${moneyTotal(cards)}M</strong>
      </div>
      <div
        className="bank__stack"
        aria-label={`${label} ${moneyTotal(cards)}M`}
      >
        {cards.slice(0, 5).map((_, index) => (
          <span
            className="bank__card"
            key={index}
            style={{ transform: `translate(${index * 5}px, ${index * 2}px)` }}
          />
        ))}
      </div>
    </div>
  );
}

function PropertyPile({
  set,
  onOpen,
}: {
  set: PropertySet;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      className="property-pile"
      style={
        {
          "--pile-color": `var(--property-${set.color}, #94a3b8)`,
        } as React.CSSProperties
      }
      onClick={onOpen}
    >
      <span className="property-pile__stripe" />
      <span className="property-pile__cards">
        {set.cards.slice(0, 5).map((card, index) => (
          <span
            className="property-pile__card"
            key={index}
            style={{ transform: `translate(${index * 8}px, ${index * 4}px)` }}
          >
            <Card card={card} size="sm" />
          </span>
        ))}
      </span>
      <span className="property-pile__count">
        {set.cards.length}
        {set.complete && " ✓"}
      </span>
    </button>
  );
}

function PlayerRow({
  player,
  title,
  onOpenPile,
  isActing,
}: {
  player: Player;
  title: string;
  onOpenPile: (set: PropertySet) => void;
  isActing: boolean;
}) {
  return (
    <section className={`player-row${isActing ? " player-row--acting" : ""}`}>
      <MiniBank cards={player.bank} />
      <div className="player-board">
        <header className="player-board__header">
          <strong>{title}</strong>
          <span>
            {player.complete_sets}/3 sets · {player.hand.size} cards
          </span>
        </header>
        <div className="property-track">
          {player.property_sets.length === 0 ? (
            <p className="empty-note">No properties yet</p>
          ) : (
            player.property_sets.map((set, index) => (
              <PropertyPile
                key={`${set.color}-${index}`}
                set={set}
                onOpen={() => onOpenPile(set)}
              />
            ))
          )}
        </div>
      </div>
    </section>
  );
}

function App() {
  const { game, loading, error, startGame, playMove } = useGame();
  const [seedInput, setSeedInput] = useState("");
  const [mctsInput, setMctsInput] = useState("");
  const [selectedHandIndex, setSelectedHandIndex] = useState<number | null>(
    null,
  );
  const [selectedDebtKeys, setSelectedDebtKeys] = useState<Set<string>>(
    new Set(),
  );
  const [discardSelection, setDiscardSelection] = useState<Set<number>>(
    new Set(),
  );
  const [modal, setModal] = useState<ModalState | null>(null);

  const viewer = game?.state.players.find(
    (player) => player.idx === game.viewer,
  );
  const opponent = game?.state.players.find(
    (player) => player.idx !== game.viewer,
  );
  const isHumanTurn = Boolean(
    game && !game.is_over && game.acting_player_idx === game.viewer,
  );
  const selectedCard = viewer?.hand.cards?.find(
    (card) => card.index === selectedHandIndex,
  );
  const pending = game?.state.pending;

  const mainPhaseMoves = useMemo(
    () =>
      selectedHandIndex === null
        ? []
        : (game?.legal_moves.filter((move) =>
            moveHasHandIndex(move, selectedHandIndex),
          ) ?? []),
    [game?.legal_moves, selectedHandIndex],
  );

  const playCandidates = async (moves: LegalMove[], title: string) => {
    if (moves.length === 0) return;
    if (moves.length === 1) {
      await playMove(moves[0].id);
      setSelectedHandIndex(null);
      return;
    }
    setModal({ title, moves });
  };

  const selectedDiscardMove = game?.legal_moves.find((move) => {
    if (move.kind !== "DiscardCards") return false;
    const selected = [...discardSelection].sort((a, b) => a - b);
    const moveIndices = (
      (move.params.hand_indices as number[] | undefined) ?? []
    )
      .map(Number)
      .sort((a, b) => a - b);
    return JSON.stringify(selected) === JSON.stringify(moveIndices);
  });

  const debtMove =
    game && viewer
      ? selectedPayDebtMove(game.legal_moves, selectedDebtKeys)
      : undefined;

  const submitMove = async (moveId: number) => {
    await playMove(moveId);
    setSelectedHandIndex(null);
    setDiscardSelection(new Set());
    setSelectedDebtKeys(new Set());
    setModal(null);
  };

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <h1>Monopoly Deal</h1>
          {game && (
            <p>
              Deck {game.state.deck_size} · Discard {game.state.discard_size} ·
              Plays {game.state.plays_this_turn}/{MAX_PLAYS}
            </p>
          )}
        </div>
        <nav className="app-nav">
          <a href="/">Game</a>
          <a href="/deck">Deck</a>
        </nav>
        <div className="new-game">
          <label>
            Seed
            <input
              type="number"
              value={seedInput}
              onChange={(event) => setSeedInput(event.target.value)}
              placeholder="random"
            />
          </label>
          <label>
            MCTS
            <input
              type="number"
              min={1}
              value={mctsInput}
              onChange={(event) => setMctsInput(event.target.value)}
              placeholder="500"
            />
          </label>
          <button
            type="button"
            onClick={() =>
              void startGame({
                seed: seedInput.trim() ? Number(seedInput) : undefined,
                mcts_iterations: mctsInput.trim()
                  ? Number(mctsInput)
                  : undefined,
              })
            }
            disabled={loading}
          >
            {game ? "New game" : "Start game"}
          </button>
        </div>
      </header>

      {error && <div className="notice notice--error">{error}</div>}
      {loading && <div className="notice">Working...</div>}

      {!game && (
        <section className="welcome">
          <p>
            Start a game. This reset keeps the card renderer and rebuilds the
            table from scratch.
          </p>
        </section>
      )}

      {game && viewer && (
        <section className="table">
          {opponent && (
            <PlayerRow
              player={opponent}
              title="Opponent"
              isActing={opponent.idx === game.acting_player_idx}
              onOpenPile={(set) =>
                setModal({
                  title: `Opponent ${labelColor(set.color)} pile`,
                  cards: set.cards,
                })
              }
            />
          )}

          <section className="center-row">
            <div className="deck-pill">
              <strong>{game.state.discard_size}</strong>
              <span>Discard</span>
            </div>
            <button
              type="button"
              className="deck-pill deck-pill--button"
              disabled={!selectedCard}
              onClick={() =>
                void playCandidates(
                  mainPhaseMoves.filter((move) =>
                    ["PlayPassGo", "PlayItsMyBirthday"].includes(move.kind),
                  ),
                  "Choose play action",
                )
              }
            >
              <strong>Play</strong>
              <span>Pass Go / Birthday</span>
            </button>
            <div className="deck-pill">
              <strong>{game.state.deck_size}</strong>
              <span>Draw</span>
            </div>
          </section>

          <section className="human-section">
            <div className="human-board-row">
              <button
                type="button"
                className="bank-target"
                disabled={!selectedCard}
                onClick={() =>
                  void playCandidates(
                    mainPhaseMoves.filter(
                      (move) => move.kind === "PlayMoneyFromHand",
                    ),
                    "Bank selected card",
                  )
                }
              >
                <MiniBank cards={viewer.bank} label="Your bank" />
              </button>
              <PlayerRow
                player={viewer}
                title="You"
                isActing={viewer.idx === game.acting_player_idx}
                onOpenPile={(set) =>
                  setModal({
                    title: `Your ${labelColor(set.color)} pile`,
                    cards: set.cards,
                  })
                }
              />
              {isHumanTurn && pending === null && (
                <div className="turn-box">
                  <strong>
                    {Math.max(0, MAX_PLAYS - game.state.plays_this_turn)}
                  </strong>
                  <span>moves left</span>
                  <button
                    type="button"
                    disabled={
                      !game.legal_moves.some((move) => move.kind === "EndTurn")
                    }
                    onClick={() => {
                      const move = game.legal_moves.find(
                        (m) => m.kind === "EndTurn",
                      );
                      if (move) void submitMove(move.id);
                    }}
                  >
                    End turn
                  </button>
                </div>
              )}
            </div>

            {pending?.kind === "PaymentDue" && (
              <section className="payment-panel">
                <h2>Pay ${String(pending.amount_m)}M</h2>
                <p>
                  Selected $
                  {viewer ? selectedDebtTotal(viewer, selectedDebtKeys) : 0}M
                </p>
                <div className="asset-row">
                  {viewer.bank.map((card, index) => {
                    const key = `money:${index}`;
                    return (
                      <button
                        type="button"
                        className={`asset-card${selectedDebtKeys.has(key) ? " is-selected" : ""}`}
                        key={key}
                        onClick={() =>
                          setSelectedDebtKeys((prev) => {
                            const next = new Set(prev);
                            if (next.has(key)) next.delete(key);
                            else next.add(key);
                            return next;
                          })
                        }
                      >
                        <Card card={card} size="sm" />
                      </button>
                    );
                  })}
                  {viewer.property_sets.flatMap((set, setIdx) =>
                    set.cards.map((card, cardIdx) => {
                      const key = `property:${setIdx}:${cardIdx}`;
                      return (
                        <button
                          type="button"
                          className={`asset-card${selectedDebtKeys.has(key) ? " is-selected" : ""}`}
                          key={key}
                          onClick={() =>
                            setSelectedDebtKeys((prev) => {
                              const next = new Set(prev);
                              if (next.has(key)) next.delete(key);
                              else next.add(key);
                              return next;
                            })
                          }
                        >
                          <Card card={card} size="sm" />
                        </button>
                      );
                    }),
                  )}
                </div>
                <button
                  type="button"
                  disabled={!debtMove}
                  onClick={() => debtMove && void submitMove(debtMove.id)}
                >
                  Pay debt
                </button>
              </section>
            )}

            <section className="hand-section">
              <h2>Your hand</h2>
              <div className="hand-row">
                {viewer.hand.cards?.map((card) => (
                  <button
                    type="button"
                    className={`hand-card${selectedHandIndex === card.index ? " is-selected" : ""}${
                      discardSelection.has(card.index) ? " is-discarded" : ""
                    }`}
                    key={card.index}
                    onClick={() => {
                      const discardOnly = game.legal_moves.every(
                        (move) => move.kind === "DiscardCards",
                      );
                      if (discardOnly) {
                        setDiscardSelection((prev) => {
                          const next = new Set(prev);
                          if (next.has(card.index)) next.delete(card.index);
                          else next.add(card.index);
                          return next;
                        });
                        return;
                      }
                      setSelectedHandIndex((prev) =>
                        prev === card.index ? null : card.index,
                      );
                    }}
                  >
                    <Card card={card} size="sm" />
                  </button>
                ))}
              </div>
              {selectedCard && (
                <div className="selected-actions">
                  <span>
                    Selected:{" "}
                    {selectedCard.display_name ??
                      selectedCard.name ??
                      selectedCard.type}
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      void playCandidates(
                        mainPhaseMoves.filter(
                          (move) => move.kind === "PlayPropertyFromHand",
                        ),
                        "Choose property pile",
                      )
                    }
                  >
                    Play to properties
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void playCandidates(
                        mainPhaseMoves.filter((move) =>
                          [
                            "PlayRent",
                            "PlayDebtCollector",
                            "PlaySlyDeal",
                            "PlayForcedDeal",
                            "PlayDealBreaker",
                          ].includes(move.kind),
                        ),
                        "Choose target action",
                      )
                    }
                  >
                    Target opponent
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void playCandidates(
                        mainPhaseMoves.filter(
                          (move) =>
                            move.kind === "PlayHouse" ||
                            move.kind === "PlayHotel",
                        ),
                        "Choose set",
                      )
                    }
                  >
                    Add to set
                  </button>
                </div>
              )}
              {selectedDiscardMove && (
                <button
                  type="button"
                  onClick={() => void submitMove(selectedDiscardMove.id)}
                >
                  Discard selected
                </button>
              )}
            </section>
          </section>

          <details className="debug">
            <summary>Legal moves</summary>
            <div className="debug-list">
              {game.legal_moves.map((move) => (
                <button
                  key={move.id}
                  type="button"
                  onClick={() => void submitMove(move.id)}
                >
                  #{move.id} {move.kind}
                </button>
              ))}
            </div>
          </details>
        </section>
      )}

      {modal && (
        <div
          className="modal-backdrop"
          onClick={() => setModal(null)}
          role="presentation"
        >
          <div
            className="modal"
            role="dialog"
            aria-label={modal.title}
            onClick={(event) => event.stopPropagation()}
          >
            <header>
              <h2>{modal.title}</h2>
              <button type="button" onClick={() => setModal(null)}>
                Close
              </button>
            </header>
            {modal.cards && (
              <div className="modal-cards">
                {modal.cards.map((card, index) => (
                  <Card key={index} card={card} />
                ))}
              </div>
            )}
            {modal.moves && (
              <div className="modal-moves">
                {modal.moves.map((move) => (
                  <button
                    key={move.id}
                    type="button"
                    onClick={() => void submitMove(move.id)}
                  >
                    <strong>{move.kind}</strong>
                    <span>{move.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

export default App;
