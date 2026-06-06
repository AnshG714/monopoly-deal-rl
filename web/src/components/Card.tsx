import type { CSSProperties } from "react";

import type { Card } from "../api/types";
import { COLOR_MAP } from "./cardColors";

const RAINBOW_COLORS = [
  "brown",
  "light_blue",
  "pink",
  "orange",
  "red",
  "yellow",
  "green",
  "blue",
  "railroad",
  "utility",
];

const ACTION_ACCENTS: Record<string, string> = {
  deal_breaker: "#7c3aed",
  debt_collector: "#c4b5fd",
  double_rent: "#f59e0b",
  forced_deal: "#64748b",
  house: "#38bdf8",
  hotel: "#f472b6",
  its_my_birthday: "#fb923c",
  just_say_no: "#67e8f9",
  pass_go: "#fde68a",
  sly_deal: "#a3a3a3",
};

const ACTION_COPY: Record<string, string> = {
  deal_breaker: "Steal a full property set from any player.",
  debt_collector: "Force any player to pay you $5M.",
  double_rent: "Play with a rent card to charge double.",
  forced_deal: "Swap one property with another player.",
  house: "Add onto a full set to raise its rent.",
  hotel: "Add onto a full set with a house.",
  its_my_birthday: "All other players pay you $2M.",
  just_say_no: "Cancel an action played against you.",
  pass_go: "Draw two extra cards.",
  sly_deal: "Steal one property from any player.",
};

const MONEY_ACCENTS: Record<number, [string, string]> = {
  1: ["#d9dfcc", "#9eaa8e"],
  2: ["#d7ccd7", "#aa96ad"],
  3: ["#cfd3cd", "#9aa09a"],
  4: ["#b9cde5", "#7895b7"],
  5: ["#9d8bd6", "#6b5aa7"],
  10: ["#d0aa38", "#9a741a"],
};

function cardTitle(card: Card): string {
  if (card.display_name) return card.display_name;
  if (card.action_type) return card.action_type.replaceAll("_", " ");
  if (card.property_kind === "single" && card.name) return card.name;
  if (card.property_kind === "multi") return `${card.color1} / ${card.color2}`;
  if (card.property_kind === "wild") return "Wild property";
  if (card.type === "rent") return `Rent ${card.color1 ?? ""}`;
  if (card.type === "wild_rent") return "Wild rent";
  if (card.type === "money") return `$${card.value}M`;
  return card.type;
}

function colorLabel(color: string): string {
  if (color === "blue" || color === "dark_blue") return "Dark Blue";
  return color
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function valueText(card: Card): string {
  return `$${card.value}M`;
}

function visualKind(card: Card): string {
  if (card.type === "money") return "money";
  if (card.action_type) return "action";
  if (card.type === "rent") return "rent";
  if (card.property_kind) return `property-${card.property_kind}`;
  return card.type;
}

function actionKindClass(card: Card): string {
  return card.action_type
    ? ` deal-card--action-${card.action_type.replaceAll("_", "-")}`
    : "";
}

function cardAccent(card: Card): string | undefined {
  if (card.color) return COLOR_MAP[card.color] ?? card.color;
  if (card.color1) return COLOR_MAP[card.color1] ?? card.color1;
  if (card.action_type) return ACTION_ACCENTS[card.action_type] ?? "#c4b5fd";
  if (card.property_kind === "wild") return COLOR_MAP.multicolor;
  if (card.type === "money") return MONEY_ACCENTS[card.value]?.[0] ?? "#d6b356";
  if (card.type === "rent") return "#d6b356";
  return undefined;
}

function cardSecondaryAccent(card: Card): string {
  if (card.type === "money") return MONEY_ACCENTS[card.value]?.[1] ?? "#9a741a";
  if (card.color2) return COLOR_MAP[card.color2] ?? card.color2;
  return cardAccent(card) ?? "#94a3b8";
}

function colorBandColors(card: Card): string[] {
  if (card.property_kind === "wild") {
    return RAINBOW_COLORS.map((color) => COLOR_MAP[color]);
  }
  if (card.color1 && card.color2) {
    return [card.color1, card.color2].map((color) => COLOR_MAP[color] ?? color);
  }
  if (card.color) return [COLOR_MAP[card.color] ?? card.color];
  return [cardAccent(card) ?? "#d6b356"];
}

function cardTypeLabel(card: Card): string {
  if (card.type === "money") return "Money Card";
  if (card.action_type) return "Action Card";
  if (card.type === "rent") return "Rent Card";
  if (card.property_kind === "wild") return "Property Wild Card";
  if (card.property_kind === "multi") return "Property Wild Card";
  if (card.property_kind === "single") return "Property Card";
  return card.type.replaceAll("_", " ");
}

function renderColorBand(card: Card) {
  return (
    <div className="deal-card__color-band">
      {colorBandColors(card).map((color, index) => (
        <span
          // Repeated colors are fine here; the index is the stable visual slot.
          key={`${color}-${index}`}
          style={{ backgroundColor: color }}
        />
      ))}
    </div>
  );
}

function renderRentLadder(
  rents: number[] | undefined,
  label?: string,
  color?: string,
) {
  if (!rents || rents.length === 0) return null;

  return (
    <div className="deal-card__rent-table">
      <span className="deal-card__rent-caption">
        {label ? `${label} rent` : "Rent"}
      </span>
      {rents.map((rent, index) => (
        <div
          className="deal-card__rent-row"
          key={`${label ?? "rent"}-${index}`}
        >
          <span
            className="deal-card__rent-count"
            style={color ? { borderTopColor: color } : undefined}
          >
            {index + 1}
          </span>
          <span className="deal-card__rent-dots" />
          <span className="deal-card__rent-value">${rent}M</span>
        </div>
      ))}
    </div>
  );
}

function renderPropertyFace(card: Card) {
  if (card.property_kind === "wild") {
    return (
      <div className="deal-card__wild-face">
        {renderColorBand(card)}
        <div className="deal-card__mascot">M</div>
        <p>This card can be used as part of any property set.</p>
      </div>
    );
  }

  if (card.property_kind === "multi") {
    const color1 = card.color1 ? COLOR_MAP[card.color1] : undefined;
    const color2 = card.color2 ? COLOR_MAP[card.color2] : undefined;

    return (
      <div className="deal-card__multi-face">
        {renderRentLadder(
          card.color1_rents,
          card.color1 ? colorLabel(card.color1) : undefined,
          color1,
        )}
        <div className="deal-card__multi-divider" />
        {renderRentLadder(
          card.color2_rents,
          card.color2 ? colorLabel(card.color2) : undefined,
          color2,
        )}
      </div>
    );
  }

  return renderRentLadder(
    card.rents,
    undefined,
    card.color ? COLOR_MAP[card.color] : undefined,
  );
}

function renderActionFace(card: Card) {
  const copy = card.action_type ? ACTION_COPY[card.action_type] : undefined;

  return (
    <div className="deal-card__action-window">
      <span>{cardTypeLabel(card)}</span>
      <strong>{cardTitle(card)}</strong>
      {copy && <p>{copy}</p>}
    </div>
  );
}

function renderRentFace(card: Card) {
  const colors = [card.color1, card.color2].filter(Boolean) as string[];

  return (
    <div className="deal-card__action-window deal-card__action-window--rent">
      <span>Action Card</span>
      <strong>Rent</strong>
      {colors.length > 0 ? (
        <div className="deal-card__rent-colors">
          {colors.map((color) => (
            <span key={color} style={{ backgroundColor: COLOR_MAP[color] }} />
          ))}
        </div>
      ) : (
        renderColorBand(card)
      )}
      <p>Charge rent for properties in the shown colors.</p>
    </div>
  );
}

function renderMoneyFace(card: Card) {
  return (
    <div className="deal-card__money-face">
      <span>{valueText(card)}</span>
    </div>
  );
}

function renderCardFace(card: Card) {
  if (card.type === "money") return renderMoneyFace(card);
  if (card.action_type) return renderActionFace(card);
  if (card.type === "rent") return renderRentFace(card);
  if (card.property_kind) return renderPropertyFace(card);
  return <div className="deal-card__action-window">{cardTitle(card)}</div>;
}

interface CardProps {
  card: Card;
  compact?: boolean;
  draggable?: boolean;
  onDragStart?: () => void;
}

export function Card({
  card,
  compact = false,
  draggable = false,
  onDragStart,
}: CardProps) {
  const accent = cardAccent(card);
  const secondaryAccent = cardSecondaryAccent(card);
  const title = cardTitle(card);

  return (
    <div
      className={`card-badge deal-card deal-card--${visualKind(card)}${actionKindClass(
        card,
      )}${compact ? " card-badge--compact deal-card--compact" : ""}${
        draggable ? " card-badge--draggable" : ""
      } card-badge--${card.type}`}
      draggable={draggable}
      onDragStart={(event) => {
        if (!draggable) return;
        event.dataTransfer.effectAllowed = "move";
        onDragStart?.();
      }}
      style={
        accent
          ? ({
              "--card-accent": accent,
              "--card-accent-2": secondaryAccent,
            } as CSSProperties)
          : undefined
      }
      title={title}
    >
      <span className="deal-card__corner deal-card__corner--top">
        {valueText(card)}
      </span>
      <div className="deal-card__frame">
        {renderColorBand(card)}
        <div className="deal-card__nameplate">
          <span>{cardTypeLabel(card)}</span>
          <strong>{title}</strong>
        </div>
        <div className="deal-card__body">{renderCardFace(card)}</div>
        <div className="deal-card__footer">© Monopoly Deal Engine</div>
      </div>
      <span className="deal-card__corner deal-card__corner--bottom">
        {valueText(card)}
      </span>
    </div>
  );
}
