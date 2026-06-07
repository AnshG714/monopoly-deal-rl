import { useEffect, useState } from "react";

import type { LegalMove, Player } from "@/api/types";
import { COLOR_MAP } from "@/components/card/colors";
import { colorLabel } from "@/components/card/utils";
import { SelectablePropertyBoard } from "@/components/SelectablePropertyBoard";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  dealBreakerTargetSets,
  findDealBreakerMove,
  findForcedDealMove,
  findSlyDealMove,
  forcedDealMyCards,
  forcedDealTheirCards,
  propertyRefLabel,
  slyDealIntoColors,
  slyDealTargetCards,
  type PropertyRef,
} from "@/lib/propertyTargets";

export type DealActionKind = "sly_deal" | "forced_deal" | "deal_breaker";

interface DealActionDialogProps {
  open: boolean;
  kind: DealActionKind;
  moves: LegalMove[];
  actor: Player;
  opponent: Player;
  existingColors: string[];
  onConfirm: (moveId: number) => void;
  onCancel: () => void;
}

type SlyStep = "pick-their-card" | "pick-into-color";
type ForcedStep = "pick-my-card" | "pick-their-card";

const COPY: Record<DealActionKind, { title: string; description: string }> = {
  sly_deal: {
    title: "Sly Deal",
    description: "Pick a property to steal from your opponent.",
  },
  forced_deal: {
    title: "Forced Deal",
    description: "Pick one of your properties to offer in a swap.",
  },
  deal_breaker: {
    title: "Deal Breaker",
    description: "Pick a complete set to steal.",
  },
};

export function DealActionDialog({
  open,
  kind,
  moves,
  actor,
  opponent,
  existingColors,
  onConfirm,
  onCancel,
}: DealActionDialogProps) {
  const [slyStep, setSlyStep] = useState<SlyStep>("pick-their-card");
  const [forcedStep, setForcedStep] = useState<ForcedStep>("pick-my-card");
  const [theirCard, setTheirCard] = useState<PropertyRef | null>(null);
  const [myCard, setMyCard] = useState<PropertyRef | null>(null);
  const [selectedSetIdx, setSelectedSetIdx] = useState<number | null>(null);

  useEffect(() => {
    if (!open) return;
    setSlyStep("pick-their-card");
    setForcedStep("pick-my-card");
    setTheirCard(null);
    setMyCard(null);
    setSelectedSetIdx(null);
  }, [open, kind, moves]);

  function handleTheirCardSelect(setIdx: number, cardIdx: number) {
    if (kind === "sly_deal") {
      const ref = { setIdx, cardIdx };
      const colors = slyDealIntoColors(moves, setIdx, cardIdx);
      if (colors.length === 1) {
        const move = findSlyDealMove(moves, setIdx, cardIdx, colors[0]);
        if (move) onConfirm(move.id);
        return;
      }
      setTheirCard(ref);
      setSlyStep("pick-into-color");
      return;
    }

    if (kind === "forced_deal" && myCard) {
      const move = findForcedDealMove(moves, myCard, { setIdx, cardIdx });
      if (move) onConfirm(move.id);
    }
  }

  function handleMyCardSelect(setIdx: number, cardIdx: number) {
    setMyCard({ setIdx, cardIdx });
    setForcedStep("pick-their-card");
  }

  function handleSetSelect(setIdx: number) {
    setSelectedSetIdx(setIdx);
    const move = findDealBreakerMove(moves, setIdx);
    if (move) onConfirm(move.id);
  }

  const copy = COPY[kind];

  let title = copy.title;
  let description = copy.description;

  if (kind === "forced_deal" && forcedStep === "pick-their-card" && myCard) {
    title = "Pick their property";
    description = `Choose what to take in exchange for ${propertyRefLabel(actor.property_sets, myCard)}.`;
  }

  if (kind === "sly_deal" && slyStep === "pick-into-color" && theirCard) {
    title = "Assign color";
    description = `Add ${propertyRefLabel(opponent.property_sets, theirCard)} to which pile?`;
  }

  const intoColors =
    kind === "sly_deal" && theirCard
      ? slyDealIntoColors(moves, theirCard.setIdx, theirCard.cardIdx)
      : [];

  const existing = new Set(existingColors);

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onCancel();
      }}
    >
      <DialogContent size="wide" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        {kind === "sly_deal" && slyStep === "pick-their-card" && (
          <SelectablePropertyBoard
            propertySets={opponent.property_sets}
            selectableCards={slyDealTargetCards(moves)}
            selectedCard={theirCard}
            onSelectCard={handleTheirCardSelect}
            emptyLabel="Opponent has no stealable properties."
          />
        )}

        {kind === "sly_deal" && slyStep === "pick-into-color" && (
          <div className="space-y-2">
            {intoColors.map((color) => (
              <Button
                key={color}
                variant="outline"
                className="h-auto w-full justify-start gap-3 px-4 py-3 text-left"
                onClick={() => {
                  if (!theirCard) return;
                  const move = findSlyDealMove(
                    moves,
                    theirCard.setIdx,
                    theirCard.cardIdx,
                    color,
                  );
                  if (move) onConfirm(move.id);
                }}
              >
                <span
                  className="size-5 shrink-0 rounded-full border border-black/10"
                  style={{ backgroundColor: COLOR_MAP[color] ?? color }}
                />
                <span>
                  <span className="block font-semibold">
                    {colorLabel(color)}
                  </span>
                  <span className="text-muted-foreground text-sm">
                    {existing.has(color) ? "Add to pile" : "Start new pile"}
                  </span>
                </span>
              </Button>
            ))}
          </div>
        )}

        {kind === "forced_deal" && forcedStep === "pick-my-card" && (
          <SelectablePropertyBoard
            propertySets={actor.property_sets}
            selectableCards={forcedDealMyCards(moves)}
            selectedCard={myCard}
            onSelectCard={handleMyCardSelect}
            emptyLabel="You have no properties to swap."
          />
        )}

        {kind === "forced_deal" &&
          forcedStep === "pick-their-card" &&
          myCard && (
            <SelectablePropertyBoard
              propertySets={opponent.property_sets}
              selectableCards={forcedDealTheirCards(
                moves,
                myCard.setIdx,
                myCard.cardIdx,
              )}
              onSelectCard={handleTheirCardSelect}
              emptyLabel="No valid swaps for that property."
            />
          )}

        {kind === "deal_breaker" && (
          <SelectablePropertyBoard
            propertySets={opponent.property_sets}
            selectableSetIndices={dealBreakerTargetSets(moves)}
            selectedSetIdx={selectedSetIdx}
            onSelectSet={handleSetSelect}
            emptyLabel="Opponent has no complete sets to steal."
          />
        )}

        <DialogFooter>
          {kind === "forced_deal" && forcedStep === "pick-their-card" && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setForcedStep("pick-my-card")}
            >
              Back
            </Button>
          )}
          {kind === "sly_deal" && slyStep === "pick-into-color" && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setSlyStep("pick-their-card")}
            >
              Back
            </Button>
          )}
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
