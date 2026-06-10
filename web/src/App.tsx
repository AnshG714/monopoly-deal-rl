import { ActionPile } from "@/components/ActionPile";
import { ActionPlayDialog } from "@/components/ActionPlayDialog";
import { Confetti } from "@/components/Confetti";
import { DealActionDialog } from "@/components/DealActionDialog";
import { DiscardCardsDialog } from "@/components/DiscardCardsDialog";
import { DebtPaymentDialog } from "@/components/DebtPaymentDialog";
import { GameControls } from "@/components/GameControls";
import { JustSayNoDialog } from "@/components/JustSayNoDialog";
import { OpponentStatus } from "@/components/OpponentStatus";
import { PlayerBank } from "@/components/PlayerBank";
import { PlayerHand } from "@/components/PlayerHand";
import { PropertyBoard } from "@/components/PropertyBoard";
import { WildPropertyColorDialog } from "@/components/WildPropertyColorDialog";
import { Flex } from "@/components/ui/flex";
import { useGame } from "@/hooks/useGame";
import { useLegalMoves } from "@/hooks/useLegalMoves";
import { dealActionKind } from "@/lib/dealActions";

export default function App() {
  const {
    game,
    loading,
    error,
    startGame,
    endGame,
    playMove,
    loadMockScenario,
    isMock,
    draggedHandIndex,
    overlay,
    pendingPrompt,
    pendingPromptOpen,
    startDrag,
    endDrag,
    openOverlay,
    closeOverlay,
    dismissPrompt,
    reopenPrompt,
  } = useGame();
  const legal = useLegalMoves(game);

  const wildPicker =
    overlay.kind === "wild-picker" || overlay.kind === "move-wild-picker"
      ? overlay
      : null;
  const actionPicker = overlay.kind === "action-picker" ? overlay : null;
  const dealAction = overlay.kind === "deal-action" ? overlay : null;
  const discardPicker = overlay.kind === "discard-picker";
  const paymentDue =
    pendingPrompt?.kind === "payment" ? pendingPrompt.payment : null;
  const jsnInterrupt =
    pendingPrompt?.kind === "jsn" ? pendingPrompt.interrupt : null;
  const showJsnModal = jsnInterrupt !== null;
  const showDebtModal = paymentDue !== null;
  const pendingActionLabel =
    pendingPrompt && !pendingPromptOpen ? pendingPrompt.label : undefined;

  const viewer = game?.state.players.find(
    (player) => player.idx === game.viewer,
  );
  const opponent = game?.state.players.find(
    (player) => player.idx !== game.viewer,
  );

  const winner = game?.is_over
    ? game.state.players.find((player) => player.idx === game.winner_idx)
    : undefined;

  const acceptsBankDrop =
    legal.canAct &&
    draggedHandIndex !== null &&
    legal.canPlayAsMoney(draggedHandIndex);

  const acceptsPropertyDrop =
    legal.canAct &&
    draggedHandIndex !== null &&
    legal.canPlayProperty(draggedHandIndex);

  const acceptsActionDrop =
    legal.canAct &&
    draggedHandIndex !== null &&
    legal.canPlayAction(draggedHandIndex);

  function handleBankDrop() {
    if (draggedHandIndex === null) return;
    const move = legal.playMoneyMove(draggedHandIndex);
    endDrag();
    if (move) void playMove(move.id);
  }

  function handlePropertyDrop() {
    if (draggedHandIndex === null) return;
    const moves = legal.playPropertyMoves(draggedHandIndex);
    if (moves.length === 0) {
      endDrag();
      return;
    }

    if (moves.length === 1) {
      endDrag();
      void playMove(moves[0].id);
      return;
    }

    openOverlay({ kind: "wild-picker", handIndex: draggedHandIndex, moves });
  }

  function handleActionDrop() {
    if (draggedHandIndex === null) return;
    const moves = legal.actionPileMoves(draggedHandIndex);
    if (moves.length === 0) {
      endDrag();
      return;
    }

    const handCard = viewer?.hand.cards?.find(
      (card) => card.index === draggedHandIndex,
    );
    const kind = dealActionKind(handCard?.action_type);
    if (kind) {
      openOverlay({
        kind: "deal-action",
        handIndex: draggedHandIndex,
        dealKind: kind,
        moves,
      });
      return;
    }

    if (moves.length === 1) {
      endDrag();
      void playMove(moves[0].id);
      return;
    }

    openOverlay({ kind: "action-picker", handIndex: draggedHandIndex, moves });
  }

  function handleActionSelect(moveId: number) {
    closeOverlay();
    void playMove(moveId);
  }

  function handleWildColorSelect(color: string) {
    if (!wildPicker) return;
    const move = wildPicker.moves.find(
      (candidate) => candidate.params.into_color === color,
    );
    closeOverlay();
    if (move) void playMove(move.id);
  }

  function handleMoveWild(fromSetIdx: number, cardIdx: number) {
    const moves = legal.moveWildMoves(fromSetIdx, cardIdx);
    if (moves.length === 0) return;
    if (moves.length === 1) {
      void playMove(moves[0].id);
      return;
    }
    openOverlay({ kind: "move-wild-picker", fromSetIdx, cardIdx, moves });
  }

  function handleNextTurn() {
    const move = legal.endTurnMove();
    if (move) void playMove(move.id);
  }

  function handlePendingMove(moveId: number) {
    if (pendingPrompt) dismissPrompt(pendingPrompt.id);
    void playMove(moveId);
  }

  function handlePendingDismiss() {
    if (pendingPrompt) dismissPrompt(pendingPrompt.id);
  }

  return (
    <Flex direction="column" className="h-screen overflow-hidden bg-page-bg">
      <GameControls
        loading={loading}
        hasGame={game !== null}
        gameOver={game?.is_over ?? false}
        canEndTurn={legal.canEndTurn()}
        canDiscard={legal.canDiscard()}
        discardCount={legal.requiredDiscardCount()}
        onOpenDiscard={() => openOverlay({ kind: "discard-picker" })}
        isMock={isMock}
        winnerName={winner?.name}
        pendingActionLabel={pendingActionLabel}
        onStartGame={() => void startGame()}
        onEndGame={endGame}
        onNextTurn={handleNextTurn}
        onReopenPendingAction={
          pendingPrompt ? reopenPrompt : undefined
        }
        onLoadMockScenario={loadMockScenario}
      />

      {!game && !loading && (
        <Flex className="flex-1" align="center" justify="center">
          <p className="text-muted-foreground text-sm">
            Press Start game to begin.
          </p>
        </Flex>
      )}

      {game && (
        <Flex
          direction="column"
          align="center"
          gap="md"
          className="min-h-0 flex-1 overflow-auto px-4 pb-4 pt-4 sm:px-6"
        >
          {opponent && (
            <>
              <OpponentStatus player={opponent} />
              <Flex
                align="end"
                justify="center"
                gap="lg"
                wrap="wrap"
                className="w-full max-w-6xl shrink-0"
              >
                <PlayerBank
                  cards={opponent.bank}
                  dialogTitle={`${opponent.name}'s bank`}
                  emptyLabel="Bank"
                />
                <PropertyBoard
                  className="min-h-0 p-0"
                  propertySets={opponent.property_sets}
                />
              </Flex>
            </>
          )}

          <Flex align="center" justify="center" className="shrink-0 py-1">
            <ActionPile
              discardSize={game.state.discard_size}
              topCard={game.state.discard_top}
              acceptsDrop={acceptsActionDrop}
              onDrop={handleActionDrop}
            />
          </Flex>

          {viewer && (
            <Flex
              align="end"
              justify="center"
              gap="lg"
              className="w-full max-w-7xl shrink-0 overflow-x-auto px-1 py-1"
            >
              <PlayerBank
                cards={viewer.bank}
                acceptsDrop={acceptsBankDrop}
                onDrop={handleBankDrop}
                dialogTitle="Your bank"
              />
              <PropertyBoard
                className="min-w-[18rem] flex-1"
                propertySets={viewer.property_sets}
                interactive
                acceptsDrop={acceptsPropertyDrop}
                onDrop={handlePropertyDrop}
                canMoveWild={legal.canMoveWild}
                onMoveWild={handleMoveWild}
              />
            </Flex>
          )}

          <Flex
            align="end"
            justify="center"
            className="h-[13rem] w-full max-w-7xl shrink-0 overflow-visible"
          >
            {viewer?.hand.cards && (
              <PlayerHand
                className="max-w-full"
                cards={viewer.hand.cards}
                canPlayAsMoney={legal.canPlayAsMoney}
                canPlayAsProperty={legal.canPlayProperty}
                canPlayAsAction={legal.canPlayAction}
                onDragStart={startDrag}
                onDragEnd={endDrag}
              />
            )}
          </Flex>
        </Flex>
      )}

      {showDebtModal && pendingPromptOpen && paymentDue && viewer?.hand.cards && (
        <DebtPaymentDialog
          key={pendingPrompt?.id}
          open
          amountOwed={paymentDue.amount_m}
          creditorName={
            game?.state.players.find(
              (player) => player.idx === paymentDue.creditor_idx,
            )?.name ?? "opponent"
          }
          player={viewer}
          handCards={viewer.hand.cards}
          legalMoves={legal.legalMoves}
          onConfirm={handlePendingMove}
          onPlayJustSayNo={handlePendingMove}
          onCancel={handlePendingDismiss}
        />
      )}

      {showJsnModal && pendingPromptOpen && jsnInterrupt && viewer?.hand.cards && (
        <JustSayNoDialog
          key={pendingPrompt?.id}
          open
          interrupt={jsnInterrupt}
          handCards={viewer.hand.cards}
          legalMoves={legal.legalMoves}
          onPlayMove={handlePendingMove}
          onCancel={handlePendingDismiss}
        />
      )}

      {dealAction && game && viewer && opponent && (
        <DealActionDialog
          key={`${dealAction.dealKind}:${dealAction.handIndex}:${dealAction.moves
            .map((move) => move.id)
            .join(",")}`}
          open
          kind={dealAction.dealKind}
          moves={dealAction.moves}
          actor={viewer}
          opponent={opponent}
          existingColors={viewer.property_sets.map((pile) => pile.color)}
          onConfirm={(moveId) => {
            closeOverlay();
            void playMove(moveId);
          }}
          onCancel={closeOverlay}
        />
      )}

      {discardPicker && viewer?.hand.cards && (
        <DiscardCardsDialog
          key={`discard:${viewer.hand.cards.map((card) => card.index).join(",")}`}
          open
          handCards={viewer.hand.cards}
          legalMoves={legal.legalMoves}
          requiredCount={legal.requiredDiscardCount()}
          onConfirm={(moveId) => {
            closeOverlay();
            void playMove(moveId);
          }}
          onCancel={closeOverlay}
        />
      )}

      {actionPicker && game && viewer && (
        <ActionPlayDialog
          open
          players={game.state.players}
          creditorPropertySets={viewer.property_sets}
          moves={actionPicker.moves}
          onSelect={handleActionSelect}
          onCancel={closeOverlay}
        />
      )}

      <WildPropertyColorDialog
        open={wildPicker !== null}
        onOpenChange={(open) => {
          if (!open) closeOverlay();
        }}
        colors={
          wildPicker
            ? [
                ...new Set(
                  wildPicker.moves.map(
                    (move) => move.params.into_color as string,
                  ),
                ),
              ]
            : []
        }
        existingColors={viewer?.property_sets.map((pile) => pile.color) ?? []}
        description={
          overlay.kind === "move-wild-picker"
            ? "Move this wild property to another color pile."
            : undefined
        }
        onSelect={handleWildColorSelect}
      />

      {error && (
        <p
          className="pointer-events-none fixed bottom-2 left-1/2 -translate-x-1/2 text-sm text-destructive"
          role="alert"
        >
          {error}
        </p>
      )}

      {game?.is_over && game.winner_idx !== null && (
        <Confetti key={`${game.game_id}-${game.winner_idx}`} />
      )}
    </Flex>
  );
}
