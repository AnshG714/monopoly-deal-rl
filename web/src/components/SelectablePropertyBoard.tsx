import type { Card, PropertySet } from "@/api/types";
import { Card as CardView } from "@/components/card";
import { COLOR_MAP } from "@/components/card/colors";
import { colorLabel } from "@/components/card/utils";
import { cn } from "@/components/ui";
import type { PropertyRef } from "@/lib/propertyTargets";

interface SelectablePropertyBoardProps {
  propertySets: PropertySet[];
  selectableCards?: PropertyRef[];
  selectedCard?: PropertyRef | null;
  onSelectCard?: (setIdx: number, cardIdx: number) => void;
  selectableSetIndices?: number[];
  selectedSetIdx?: number | null;
  onSelectSet?: (setIdx: number) => void;
  emptyLabel?: string;
}

function isCardSelected(
  selected: PropertyRef | null | undefined,
  setIdx: number,
  cardIdx: number,
): boolean {
  return selected?.setIdx === setIdx && selected?.cardIdx === cardIdx;
}

function canSelectCard(
  selectableCards: PropertyRef[] | undefined,
  setIdx: number,
  cardIdx: number,
): boolean {
  if (!selectableCards) return true;
  return selectableCards.some(
    (ref) => ref.setIdx === setIdx && ref.cardIdx === cardIdx,
  );
}

function PileCards({
  cards,
  setIdx,
  selectableCards,
  selectedCard,
  onSelectCard,
}: {
  cards: Card[];
  setIdx: number;
  selectableCards?: PropertyRef[];
  selectedCard?: PropertyRef | null;
  onSelectCard?: (setIdx: number, cardIdx: number) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {cards.map((card, cardIdx) => {
        const enabled = canSelectCard(selectableCards, setIdx, cardIdx);
        const selected = isCardSelected(selectedCard, setIdx, cardIdx);
        return (
          <CardView
            key={cardIdx}
            card={card}
            size="sm"
            onClick={
              enabled && onSelectCard
                ? () => onSelectCard(setIdx, cardIdx)
                : undefined
            }
            className={cn(
              !enabled && "opacity-40",
              selected && "rounded-xl ring-2 ring-green-500",
            )}
          />
        );
      })}
    </div>
  );
}

export function SelectablePropertyBoard({
  propertySets,
  selectableCards,
  selectedCard,
  onSelectCard,
  selectableSetIndices,
  selectedSetIdx,
  onSelectSet,
  emptyLabel = "No properties",
}: SelectablePropertyBoardProps) {
  if (propertySets.length === 0) {
    return <p className="text-muted-foreground text-sm">{emptyLabel}</p>;
  }

  if (selectableSetIndices && onSelectSet) {
    return (
      <div className="space-y-4">
        {propertySets.map((pile, setIdx) => {
          if (!selectableSetIndices.includes(setIdx)) return null;
          const selected = selectedSetIdx === setIdx;
          const accent = COLOR_MAP[pile.color] ?? pile.color;
          return (
            <button
              key={pile.color}
              type="button"
              className={cn(
                "w-full rounded-lg border p-4 text-left transition-colors",
                selected
                  ? "border-green-500 bg-green-50"
                  : "border-[var(--color-border)] hover:bg-[var(--color-hint-bg)]",
              )}
              onClick={() => onSelectSet(setIdx)}
            >
              <div className="mb-3 flex items-center gap-2">
                <span
                  className="size-3 rounded-full border border-black/10"
                  style={{ backgroundColor: accent }}
                />
                <span className="font-semibold">
                  {colorLabel(pile.color)} · complete
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {pile.cards.map((card, cardIdx) => (
                  <CardView key={cardIdx} card={card} size="sm" />
                ))}
              </div>
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {propertySets.map((pile, setIdx) => {
        const pileCards = pile.cards.map((_, cardIdx) => cardIdx);
        const hasSelectable = selectableCards
          ? pileCards.some((cardIdx) =>
              canSelectCard(selectableCards, setIdx, cardIdx),
            )
          : pile.cards.length > 0;
        if (!hasSelectable) return null;

        const accent = COLOR_MAP[pile.color] ?? pile.color;
        return (
          <div key={pile.color} className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span
                className="size-3 rounded-full border border-black/10"
                style={{ backgroundColor: accent }}
              />
              {colorLabel(pile.color)}
              {pile.complete && (
                <span className="text-muted-foreground font-normal">
                  · complete
                </span>
              )}
            </div>
            <PileCards
              cards={pile.cards}
              setIdx={setIdx}
              selectableCards={selectableCards}
              selectedCard={selectedCard}
              onSelectCard={onSelectCard}
            />
          </div>
        );
      })}
    </div>
  );
}
