import type { LegalMove, Player, PropertySet } from "@/api/types";
import { COLOR_MAP } from "@/components/card/colors";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  actionDialogContext,
  actionMoveDescription,
} from "@/lib/actionMoves";

interface ActionPlayDialogProps {
  open: boolean;
  players: Player[];
  creditorPropertySets: PropertySet[];
  moves: LegalMove[];
  onSelect: (moveId: number) => void;
  onCancel: () => void;
}

export function ActionPlayDialog({
  open,
  players,
  creditorPropertySets,
  moves,
  onSelect,
  onCancel,
}: ActionPlayDialogProps) {
  const { title, description } = actionDialogContext(moves);

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onCancel();
      }}
    >
      <DialogContent showCloseButton={false} size="wide">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          {moves.map((move) => {
            const { title: optionTitle, subtitle, accentColor } =
              actionMoveDescription(move, players, creditorPropertySets);

            return (
              <Button
                key={move.id}
                variant="outline"
                className="h-auto w-full justify-start gap-3 px-4 py-3 text-left"
                onClick={() => onSelect(move.id)}
              >
                {accentColor && (
                  <span
                    className="size-5 shrink-0 rounded-full border border-black/10"
                    style={{
                      backgroundColor: COLOR_MAP[accentColor] ?? accentColor,
                    }}
                  />
                )}
                <span className="min-w-0">
                  <span className="block font-semibold">{optionTitle}</span>
                  {subtitle && (
                    <span className="text-muted-foreground mt-1 block text-sm">
                      {subtitle}
                    </span>
                  )}
                </span>
              </Button>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
