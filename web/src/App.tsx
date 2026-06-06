import { useEffect, useState } from "react";

import type { LegalMove } from "@/api/types";
import { ActionPile } from "@/components/ActionPile";
import { ActionPlayDialog } from "@/components/ActionPlayDialog";
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
import { viewerJustSayNoInterrupt } from "@/lib/interrupts";
import { viewerMustPayDebt } from "@/lib/payDebt";

interface MovePickerState {
  handIndex: number;
  moves: LegalMove[];
}

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
  } = useGame();
  const legal = useLegalMoves(game);
  const [draggedHandIndex, setDraggedHandIndex] = useState<number | null>(null);
  const [wildPicker, setWildPicker] = useState<MovePickerState | null>(null);
  const [actionPicker, setActionPicker] = useState<MovePickerState | null>(
    null,
  );
  const [pendingModalDismissed, setPendingModalDismissed] = useState(false);

  const paymentDue = game ? viewerMustPayDebt(game) : null;
  const jsnInterrupt = game
    ? viewerJustSayNoInterrupt(game, legal.legalMoves)
    : null;
  const showJsnModal = jsnInterrupt !== null;
  const showDebtModal = paymentDue !== null && !showJsnModal;
  const pendingModalOpen =
    (showDebtModal || showJsnModal) && !pendingModalDismissed;

  const pendingActionKey =
    jsnInterrupt?.key ??
    (paymentDue
      ? `PaymentDue:${paymentDue.creditor_idx}:${paymentDue.amount_m}`
      : null);

  useEffect(() => {
    setPendingModalDismissed(false);
  }, [pendingActionKey, game?.game_id]);

  const pendingActionLabel = (() => {
    if (!pendingModalDismissed) return undefined;
    if (jsnInterrupt) return `Respond: ${jsnInterrupt.title}`;
    if (paymentDue) return `Pay $${paymentDue.amount_m}M`;
    return undefined;
  })();

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
    if (move) void playMove(move.id);
    setDraggedHandIndex(null);
  }

  function handlePropertyDrop() {
    if (draggedHandIndex === null) return;
    const moves = legal.playPropertyMoves(draggedHandIndex);
    if (moves.length === 0) return;

    if (moves.length === 1) {
      void playMove(moves[0].id);
      setDraggedHandIndex(null);
      return;
    }

    setWildPicker({ handIndex: draggedHandIndex, moves });
    setDraggedHandIndex(null);
  }

  function handleActionDrop() {
    if (draggedHandIndex === null) return;
    const moves = legal.actionPileMoves(draggedHandIndex);
    if (moves.length === 0) return;

    if (moves.length === 1) {
      void playMove(moves[0].id);
      setDraggedHandIndex(null);
      return;
    }

    setActionPicker({ handIndex: draggedHandIndex, moves });
    setDraggedHandIndex(null);
  }

  function handleActionSelect(moveId: number) {
    void playMove(moveId);
    setActionPicker(null);
  }

  function handleWildColorSelect(color: string) {
    if (!wildPicker) return;
    const move = wildPicker.moves.find(
      (candidate) => candidate.params.into_color === color,
    );
    if (move) void playMove(move.id);
    setWildPicker(null);
  }

  function handleNextTurn() {
    const move = legal.endTurnMove();
    if (move) void playMove(move.id);
  }

  return (
    <Flex direction="column" className="h-screen overflow-hidden bg-page-bg">
      <GameControls
        loading={loading}
        hasGame={game !== null}
        gameOver={game?.is_over ?? false}
        canEndTurn={legal.canEndTurn()}
        isMock={isMock}
        winnerName={winner?.name}
        pendingActionLabel={pendingActionLabel}
        onStartGame={() => void startGame()}
        onEndGame={endGame}
        onNextTurn={handleNextTurn}
        onReopenPendingAction={
          showDebtModal || showJsnModal
            ? () => setPendingModalDismissed(false)
            : undefined
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
                onDragStart={setDraggedHandIndex}
                onDragEnd={() => setDraggedHandIndex(null)}
              />
            )}
          </Flex>
        </Flex>
      )}

      {showDebtModal && paymentDue && viewer?.hand.cards && (
        <DebtPaymentDialog
          open={pendingModalOpen}
          amountOwed={paymentDue.amount_m}
          creditorName={
            game?.state.players.find(
              (player) => player.idx === paymentDue.creditor_idx,
            )?.name ?? "opponent"
          }
          player={viewer}
          handCards={viewer.hand.cards}
          legalMoves={legal.legalMoves}
          onConfirm={(moveId) => {
            setPendingModalDismissed(true);
            void playMove(moveId);
          }}
          onPlayJustSayNo={(moveId) => {
            setPendingModalDismissed(true);
            void playMove(moveId);
          }}
          onCancel={() => setPendingModalDismissed(true)}
        />
      )}

      {showJsnModal && jsnInterrupt && viewer?.hand.cards && (
        <JustSayNoDialog
          open={pendingModalOpen}
          interrupt={jsnInterrupt}
          handCards={viewer.hand.cards}
          legalMoves={legal.legalMoves}
          onPlayMove={(moveId) => {
            setPendingModalDismissed(true);
            void playMove(moveId);
          }}
          onCancel={() => setPendingModalDismissed(true)}
        />
      )}

      {actionPicker && game && viewer && (
        <ActionPlayDialog
          open
          players={game.state.players}
          creditorPropertySets={viewer.property_sets}
          moves={actionPicker.moves}
          onSelect={handleActionSelect}
          onCancel={() => setActionPicker(null)}
        />
      )}

      <WildPropertyColorDialog
        open={wildPicker !== null}
        onOpenChange={(open) => {
          if (!open) setWildPicker(null);
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
    </Flex>
  );
}
