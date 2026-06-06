import { COLOR_MAP } from "@/components/card/colors";
import { colorLabel } from "@/components/card/utils";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Flex } from "@/components/ui/flex";

interface WildPropertyColorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  colors: string[];
  existingColors: string[];
  onSelect: (color: string) => void;
}

export function WildPropertyColorDialog({
  open,
  onOpenChange,
  colors,
  existingColors,
  onSelect,
}: WildPropertyColorDialogProps) {
  const existing = new Set(existingColors);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton={false} className="min-w-fit">
        <DialogHeader>
          <DialogTitle>Choose a color</DialogTitle>
          <DialogDescription>
            Assign this wild property to a color pile.
          </DialogDescription>
        </DialogHeader>

        <Flex direction="column" gap="sm">
          {colors.map((color) => (
            <Button
              key={color}
              variant="outline"
              className="h-auto w-full justify-start gap-3 px-4 py-3 text-left"
              onClick={() => onSelect(color)}
            >
              <span
                className="size-5 shrink-0 rounded-full border border-black/10"
                style={{ backgroundColor: COLOR_MAP[color] ?? color }}
              />
              <span className="min-w-0">
                <span className="block text-base font-semibold leading-5">
                  {colorLabel(color)}
                </span>
                <span className="text-muted-foreground mt-1 block text-sm leading-5">
                  {existing.has(color) ? "Add to pile" : "Start new pile"}
                </span>
              </span>
            </Button>
          ))}
        </Flex>
      </DialogContent>
    </Dialog>
  );
}
