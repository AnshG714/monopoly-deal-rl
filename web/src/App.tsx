import { useEffect } from "react";

import { CARD_SIZES } from "@/components/card/constants";
import { PlayerHand } from "@/components/PlayerHand";
import { Flex } from "@/components/ui/flex";
import { useGame } from "@/hooks/useGame";

export default function App() {
  const { game, loading, error, startGame } = useGame();

  useEffect(() => {
    void startGame();
  }, [startGame]);

  const viewer = game?.state.players.find(
    (player) => player.idx === game.viewer,
  );
  const opponent = game?.state.players.find(
    (player) => player.idx !== game.viewer,
  );

  return (
    <Flex direction="column" className="h-screen bg-page-bg">
      <Flex
        className="h-full overflow-x-auto px-6 pt-6"
        align="start"
        justify="center"
        gap="md"
      >
        {opponent && (
          <Flex gap="md">
            {Array.from({ length: opponent.hand.size }, (_, index) => (
              <div
                key={index}
                className="shrink-0 rounded-[14px] bg-surface-muted"
                style={{
                  width: CARD_SIZES.sm,
                  aspectRatio: "12 / 17.15",
                }}
              />
            ))}
          </Flex>
        )}
      </Flex>

      <Flex
        className="shrink-0 overflow-visible px-6 pb-6"
        align="end"
        justify="center"
      >
        {viewer?.hand.cards && <PlayerHand cards={viewer.hand.cards} />}
      </Flex>

      {(loading || error) && (
        <p className="pointer-events-none fixed bottom-2 left-1/2 -translate-x-1/2 text-sm text-[var(--text-muted)]">
          {error ?? "Loading…"}
        </p>
      )}
    </Flex>
  );
}
