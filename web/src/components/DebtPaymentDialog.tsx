import { useEffect, useMemo, useState } from "react";

import type { Card, HandCard, LegalMove, Player, PropertySet } from "@/api/types";
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
import { cn } from "@/components/ui";
import {
  findPayDebtMove,
  isValidPaymentSelection,
  paymentSelectionTotal,
} from "@/lib/payDebt";
import { findPlayJustSayNoMove } from "@/lib/interrupts";

interface DebtPaymentDialogProps {
  open: boolean;
  amountOwed: number;
  creditorName: string;
  player: Player;
  handCards: HandCard[];
  legalMoves: LegalMove[];
  onConfirm: (moveId: number) => void;
  onPlayJustSayNo?: (moveId: number) => void;
  onCancel: () => void;
}

function propertyKey(setIdx: number, cardIdx: number): string {
  return `${setIdx}:${cardIdx}`;
}

function SelectableCard({
  card,
  selected,
  onToggle,
}: {
  card: Card;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <CardView
      card={card}
      size="sm"
      onClick={onToggle}
      className={cn(selected && "rounded-xl ring-2 ring-green-500")}
    />
  );
}

function PropertySection({
  propertySets,
  selectedKeys,
  onToggle,
}: {
  propertySets: PropertySet[];
  selectedKeys: Set<string>;
  onToggle: (setIdx: number, cardIdx: number) => void;
}) {
  if (propertySets.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">No properties to offer.</p>
    );
  }

  return (
    <div className="space-y-4">
      {propertySets.map((pile, setIdx) => (
        <div key={pile.color} className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <span
              className="size-3 rounded-full border border-black/10"
              style={{ backgroundColor: COLOR_MAP[pile.color] ?? pile.color }}
            />
            {colorLabel(pile.color)}
          </div>
          <div className="flex flex-wrap gap-2">
            {pile.cards.map((card, cardIdx) => (
              <SelectableCard
                key={propertyKey(setIdx, cardIdx)}
                card={card}
                selected={selectedKeys.has(propertyKey(setIdx, cardIdx))}
                onToggle={() => onToggle(setIdx, cardIdx)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function SummaryRow({
  label,
  value,
  valueClassName,
}: {
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border px-4 py-3">
      <span className="text-sm font-medium">{label}</span>
      <span className={cn("text-base font-semibold", valueClassName)}>
        {value}
      </span>
    </div>
  );
}

export function DebtPaymentDialog({
  open,
  amountOwed,
  creditorName,
  player,
  handCards,
  legalMoves,
  onConfirm,
  onPlayJustSayNo,
  onCancel,
}: DebtPaymentDialogProps) {
  const [selectedMoney, setSelectedMoney] = useState<number[]>([]);
  const [selectedProperties, setSelectedProperties] = useState<
    [number, number][]
  >([]);

  useEffect(() => {
    if (!open) return;
    setSelectedMoney([]);
    setSelectedProperties([]);
  }, [open, amountOwed]);

  const selectedTotal = useMemo(
    () =>
      paymentSelectionTotal(
        selectedMoney,
        selectedProperties,
        player.bank,
        player.property_sets,
      ),
    [player.bank, player.property_sets, selectedMoney, selectedProperties],
  );

  const validSelection = isValidPaymentSelection(
    selectedMoney,
    selectedProperties,
    player.bank,
    player.property_sets,
    amountOwed,
  );

  const matchingMove = validSelection
    ? findPayDebtMove(legalMoves, selectedMoney, selectedProperties)
    : undefined;

  const jsnHandIndices = handCards
    .filter(
      (card) =>
        card.action_type === "just_say_no" &&
        findPlayJustSayNoMove(legalMoves, card.index) !== undefined,
    )
    .map((card) => card.index);

  const propertySelectedKeys = useMemo(
    () =>
      new Set(
        selectedProperties.map(([setIdx, cardIdx]) =>
          propertyKey(setIdx, cardIdx),
        ),
      ),
    [selectedProperties],
  );

  function toggleMoney(index: number) {
    setSelectedMoney((current) =>
      current.includes(index)
        ? current.filter((value) => value !== index)
        : [...current, index],
    );
  }

  function toggleProperty(setIdx: number, cardIdx: number) {
    const key = propertyKey(setIdx, cardIdx);
    setSelectedProperties((current) => {
      const exists = current.some(
        ([valueSetIdx, valueCardIdx]) =>
          propertyKey(valueSetIdx, valueCardIdx) === key,
      );
      if (exists) {
        return current.filter(
          ([valueSetIdx, valueCardIdx]) =>
            propertyKey(valueSetIdx, valueCardIdx) !== key,
        );
      }
      return [...current, [setIdx, cardIdx]];
    });
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onCancel();
      }}
    >
      <DialogContent size="wide" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Pay ${amountOwed}M</DialogTitle>
          <DialogDescription>
            Select cards from your bank and properties to pay {creditorName}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <SummaryRow label="Amount owed" value={`$${amountOwed}M`} />
          <SummaryRow
            label="Selected total"
            value={`$${selectedTotal}M`}
            valueClassName={validSelection ? "text-green-600" : undefined}
          />

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Bank</h3>
            {player.bank.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No money in your bank.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {player.bank.map((card, index) => (
                  <SelectableCard
                    key={index}
                    card={card}
                    selected={selectedMoney.includes(index)}
                    onToggle={() => toggleMoney(index)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Properties</h3>
            <PropertySection
              propertySets={player.property_sets}
              selectedKeys={propertySelectedKeys}
              onToggle={toggleProperty}
            />
          </section>

          {onPlayJustSayNo && jsnHandIndices.length > 0 && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">Or play Just Say No</h3>
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
                      onClick={() => onPlayJustSayNo(move.id)}
                    />
                  );
                })}
              </div>
            </section>
          )}
        </div>

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
            Confirm payment
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
