import type { HandCard, LegalMove } from "@/api/types";
import { Card as CardView } from "@/components/card";
import { COLOR_MAP } from "@/components/card/colors";
import { colorLabel } from "@/components/card/utils";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { JustSayNoInterrupt } from "@/lib/interrupts";
import { findPassJustSayNoMove, findPlayJustSayNoMove } from "@/lib/interrupts";

interface JustSayNoDialogProps {
  open: boolean;
  interrupt: JustSayNoInterrupt;
  handCards: HandCard[];
  legalMoves: LegalMove[];
  onPlayMove: (moveId: number) => void;
  onCancel: () => void;
}

function ColorLabel({ color }: { color: string }) {
  return (
    <div className="text-muted-foreground flex items-center gap-2 text-sm">
      <span
        className="size-3 rounded-full border border-black/10"
        style={{ backgroundColor: COLOR_MAP[color] ?? color }}
      />
      {colorLabel(color)}
    </div>
  );
}

export function JustSayNoDialog({
  open,
  interrupt,
  handCards,
  legalMoves,
  onPlayMove,
  onCancel,
}: JustSayNoDialogProps) {
  const passMove = findPassJustSayNoMove(legalMoves);
  const jsnHandIndices = handCards
    .filter(
      (card) =>
        card.action_type === "just_say_no" &&
        findPlayJustSayNoMove(legalMoves, card.index) !== undefined,
    )
    .map((card) => card.index);

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onCancel();
      }}
    >
      <DialogContent size="wide" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>{interrupt.title}</DialogTitle>
          <DialogDescription>{interrupt.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {interrupt.targetCard && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">
                {interrupt.swapOfferCard ? "Your property" : "Target property"}
              </h3>
              {interrupt.targetColor && (
                <ColorLabel color={interrupt.targetColor} />
              )}
              <CardView card={interrupt.targetCard} size="sm" />
            </section>
          )}

          {interrupt.swapOfferCard && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">Offered in exchange</h3>
              {interrupt.swapOfferColor && (
                <ColorLabel color={interrupt.swapOfferColor} />
              )}
              <CardView card={interrupt.swapOfferCard} size="sm" />
            </section>
          )}

          {interrupt.stolenSet && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">Complete set at risk</h3>
              {interrupt.targetColor && (
                <ColorLabel color={interrupt.targetColor} />
              )}
              <div className="flex flex-wrap gap-2">
                {interrupt.stolenSet.cards.map((card, index) => (
                  <CardView key={index} card={card} size="sm" />
                ))}
              </div>
            </section>
          )}

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Just Say No</h3>
            {jsnHandIndices.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                You have no Just Say No cards to play.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {jsnHandIndices.map((handIndex) => {
                  const card = handCards.find(
                    (candidate) => candidate.index === handIndex,
                  );
                  const move = findPlayJustSayNoMove(legalMoves, handIndex);
                  if (!card || !move) return null;
                  return (
                    <CardView
                      key={handIndex}
                      card={card}
                      size="sm"
                      onClick={() => onPlayMove(move.id)}
                    />
                  );
                })}
              </div>
            )}
          </section>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          {passMove && (
            <Button type="button" onClick={() => onPlayMove(passMove.id)}>
              {interrupt.allowLabel}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
