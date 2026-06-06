import type { Player } from "../api/types";
import { Card } from "./Card";
import { COLOR_MAP } from "./cardColors";

interface PlayerPanelProps {
  player: Player;
  isViewer: boolean;
  isActing: boolean;
  isCurrentTurn: boolean;
  canDragHandCards?: boolean;
  canDropOnProperties?: boolean;
  onHandCardDragStart?: (handIndex: number) => void;
  onDropOnPropertySet?: (setIdx: number, color: string) => void;
}

function bankTotal(bank: Player["bank"]): number {
  return bank.reduce((sum, card) => sum + card.value, 0);
}

export function PlayerPanel({
  player,
  isViewer,
  isActing,
  isCurrentTurn,
  canDragHandCards = false,
  canDropOnProperties = false,
  onHandCardDragStart,
  onDropOnPropertySet,
}: PlayerPanelProps) {
  const status = [isActing ? "acting" : null, isCurrentTurn ? "turn" : null]
    .filter(Boolean)
    .join(" · ");

  return (
    <section
      className={`player-panel${isViewer ? " player-panel--viewer" : ""}${
        isActing ? " player-panel--acting" : ""
      }`}
    >
      <header className="player-panel__header">
        <h2>{player.name}</h2>
        {status && <span className="player-panel__status">{status}</span>}
      </header>

      <dl className="player-panel__stats">
        <div>
          <dt>Complete sets</dt>
          <dd>{player.complete_sets} / 3</dd>
        </div>
        <div>
          <dt>Bank</dt>
          <dd>${bankTotal(player.bank)}M</dd>
        </div>
        <div>
          <dt>Hand</dt>
          <dd>{player.hand.size} cards</dd>
        </div>
      </dl>

      {isViewer && player.hand.cards && (
        <div className="player-panel__hand">
          <h3>Your hand</h3>
          <div className="card-row">
            {player.hand.cards.map((card) => (
              <Card
                key={card.index}
                card={card}
                draggable={canDragHandCards}
                onDragStart={() => onHandCardDragStart?.(card.index)}
              />
            ))}
          </div>
        </div>
      )}

      <div className="player-panel__properties">
        <h3>Properties</h3>
        {player.property_sets.length === 0 ? (
          <p className="muted">No property sets yet.</p>
        ) : (
          <ul className="property-set-list">
            {player.property_sets.map((set, idx) => (
              <li
                key={`${set.color}-${idx}`}
                className={`property-set${
                  canDropOnProperties ? " property-set--drop-target" : ""
                }`}
                onDragOver={(event) => {
                  if (!canDropOnProperties) return;
                  event.preventDefault();
                  event.dataTransfer.dropEffect = "move";
                }}
                onDrop={(event) => {
                  if (!canDropOnProperties) return;
                  event.preventDefault();
                  onDropOnPropertySet?.(idx, set.color);
                }}
              >
                <div className="property-set__header">
                  <span
                    className="property-set__color"
                    style={{
                      backgroundColor:
                        set.color in COLOR_MAP ? COLOR_MAP[set.color] : "#ccc",
                    }}
                  />
                  <span className="property-set__label">
                    {set.color.replaceAll("_", " ")}
                    {set.complete && " ✓"}
                    {set.has_house && " +house"}
                    {set.has_hotel && " +hotel"}
                  </span>
                </div>
                <div className="card-row card-row--compact">
                  {set.cards.map((card, cardIdx) => (
                    <Card key={cardIdx} card={card} compact />
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
