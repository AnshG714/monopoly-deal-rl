import { Button } from "@/components/ui/button";
import { Flex } from "@/components/ui/flex";
import { MOCK_SCENARIOS } from "@/mocks";

interface GameControlsProps {
  loading: boolean;
  hasGame: boolean;
  gameOver: boolean;
  canEndTurn: boolean;
  isMock?: boolean;
  winnerName?: string;
  pendingActionLabel?: string;
  onStartGame: () => void;
  onEndGame: () => void;
  onNextTurn: () => void;
  onReopenPendingAction?: () => void;
  onLoadMockScenario?: (scenarioId: string) => void;
}

export function GameControls({
  loading,
  hasGame,
  gameOver,
  canEndTurn,
  isMock = false,
  winnerName,
  pendingActionLabel,
  onStartGame,
  onEndGame,
  onNextTurn,
  onReopenPendingAction,
  onLoadMockScenario,
}: GameControlsProps) {
  const showMockPicker =
    import.meta.env.DEV && onLoadMockScenario !== undefined;
  return (
    <Flex
      align="center"
      justify="between"
      gap="md"
      wrap="wrap"
      className="shrink-0 border-b border-[var(--color-border)] bg-white/80 px-6 py-3"
    >
      <Flex direction="column" gap="none">
        <span className="text-sm font-semibold">Monopoly Deal</span>
        {gameOver && winnerName && (
          <span className="text-muted-foreground text-xs">
            {winnerName} wins
          </span>
        )}
        {hasGame && !gameOver && loading && (
          <span className="text-muted-foreground text-xs">Updating…</span>
        )}
        {isMock && (
          <span className="text-xs font-medium text-amber-700">
            Mock UI state — moves stay local
          </span>
        )}
      </Flex>

      <Flex gap="sm" wrap="wrap" align="center">
        {showMockPicker && (
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground whitespace-nowrap">
              Load mock
            </span>
            <select
              className="h-8 min-w-[11rem] rounded-md border border-[var(--color-border)] bg-white px-2 text-sm"
              defaultValue=""
              onChange={(event) => {
                const scenarioId = event.target.value;
                if (scenarioId) onLoadMockScenario(scenarioId);
                event.target.value = "";
              }}
            >
              <option value="" disabled>
                Pick scenario…
              </option>
              {MOCK_SCENARIOS.map((scenario) => (
                <option key={scenario.id} value={scenario.id}>
                  {scenario.label}
                </option>
              ))}
            </select>
          </label>
        )}
        {pendingActionLabel && onReopenPendingAction && (
          <Button
            size="sm"
            variant="default"
            onClick={onReopenPendingAction}
            disabled={loading}
          >
            {pendingActionLabel}
          </Button>
        )}
        <Button
          size="sm"
          className="bg-accent text-accent-foreground hover:bg-accent/90"
          onClick={onStartGame}
          disabled={loading || (hasGame && !gameOver)}
        >
          Start game
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={onEndGame}
          disabled={!hasGame || loading}
        >
          End game
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={onNextTurn}
          disabled={!canEndTurn || loading}
        >
          Next turn
        </Button>
      </Flex>
    </Flex>
  );
}
