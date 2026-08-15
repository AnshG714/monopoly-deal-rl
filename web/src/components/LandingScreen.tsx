import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Flex } from "@/components/ui/flex";
import { Label } from "@/components/ui/label";

export interface AiConfig {
  useValueNet: boolean;
  usePolicyNet: boolean;
}

interface LandingScreenProps {
  config: AiConfig;
  loading: boolean;
  onChange: (config: AiConfig) => void;
  onStart: () => void;
}

function ToggleRow({
  id,
  checked,
  title,
  description,
  onCheckedChange,
}: {
  id: string;
  checked: boolean;
  title: string;
  description: string;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <Label
      htmlFor={id}
      className="w-full items-start gap-3 rounded-lg border border-[var(--color-border)] p-3 font-normal"
    >
      <input
        id={id}
        type="checkbox"
        className="mt-0.5 size-4 shrink-0 accent-accent"
        checked={checked}
        onChange={(event) => onCheckedChange(event.target.checked)}
      />
      <Flex direction="column" gap="none" className="min-w-0 flex-1">
        <span className="text-sm font-medium">{title}</span>
        <span className="text-muted-foreground text-xs">{description}</span>
      </Flex>
    </Label>
  );
}

export function LandingScreen({
  config,
  loading,
  onChange,
  onStart,
}: LandingScreenProps) {
  return (
    <Flex
      direction="column"
      justify="center"
      className="min-h-0 w-full flex-1 overflow-auto px-4 py-8"
    >
      <Card className="mx-auto w-full max-w-md shrink-0">
        <CardHeader>
          <CardTitle className="text-xl">New game</CardTitle>
          <CardDescription>
            Choose how the AI opponent searches. Heuristic MCTS is always on;
            nets are optional extras.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Flex direction="column" gap="md">
            <ToggleRow
              id="use-value-net"
              checked={config.useValueNet}
              title="Value net"
              description="Use the trained net at MCTS leaves instead of the handcrafted evaluator."
              onCheckedChange={(useValueNet) =>
                onChange({ ...config, useValueNet })
              }
            />
            <ToggleRow
              id="use-policy-net"
              checked={config.usePolicyNet}
              title="Policy net"
              description="Use the trained net to rank and prune candidate moves."
              onCheckedChange={(usePolicyNet) =>
                onChange({ ...config, usePolicyNet })
              }
            />
            <Button
              className="bg-accent text-accent-foreground hover:bg-accent/90"
              onClick={onStart}
              disabled={loading}
            >
              {loading ? "Starting…" : "Start game"}
            </Button>
          </Flex>
        </CardContent>
      </Card>
    </Flex>
  );
}
