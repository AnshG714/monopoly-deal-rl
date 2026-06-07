import { useEffect, useMemo, useState } from "react";

import type { HandCard, LegalMove } from "@/api/types";
import { Card as CardView } from "@/components/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn, Flex } from "@/components/ui";
import { findDiscardMove } from "@/lib/discardCards";

interface DiscardCardsDialogProps {
  open: boolean;
  handCards: HandCard[];
  legalMoves: LegalMove[];
  requiredCount: number;
  onConfirm: (moveId: number) => void;
  onCancel: () => void;
}

export function DiscardCardsDialog({
  open,
  handCards,
  legalMoves,
  requiredCount,
  onConfirm,
  onCancel,
}: DiscardCardsDialogProps) {
  const [selected, setSelected] = useState<number[]>([]);

  useEffect(() => {
    if (open) setSelected([]);
  }, [open]);

  const matchingMove = useMemo(() => {
    if (selected.length !== requiredCount) return undefined;
    return findDiscardMove(legalMoves, selected);
  }, [legalMoves, requiredCount, selected]);

  function toggleHandIndex(handIndex: number) {
    setSelected((current) => {
      if (current.includes(handIndex)) {
        return current.filter((value) => value !== handIndex);
      }
      if (current.length >= requiredCount) {
        return current;
      }
      return [...current, handIndex];
    });
  }

  const countLabel =
    requiredCount === 1 ? "1 card" : `${requiredCount} cards`;

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onCancel();
      }}
    >
      <DialogContent size="wide" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Discard cards</DialogTitle>
          <DialogDescription>
            Select exactly {countLabel} to discard down to 7.
          </DialogDescription>
        </DialogHeader>

        <Flex direction="column" gap="md">
          <Flex
            align="center"
            justify="between"
            className="rounded-lg border px-4 py-3"
          >
            <span className="text-sm font-medium">Selected</span>
            <span
              className={cn(
                "text-base font-semibold",
                matchingMove && "text-green-600",
              )}
            >
              {selected.length} / {requiredCount}
            </span>
          </Flex>

          <Flex wrap="wrap" gap="sm">
            {handCards.map((card) => (
              <CardView
                key={card.index}
                card={card}
                size="sm"
                onClick={() => toggleHandIndex(card.index)}
                className={cn(
                  selected.includes(card.index) &&
                    "rounded-xl ring-2 ring-green-500",
                )}
              />
            ))}
          </Flex>
        </Flex>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            type="button"
            disabled={!matchingMove}
            onClick={() => {
              if (matchingMove) onConfirm(matchingMove.id);
            }}
          >
            Confirm discard
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
