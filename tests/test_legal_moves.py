from __future__ import annotations

import unittest

from models.cards.action import (
    ActionCard,
    ActionCardType,
    DebtCollector,
    PassGo,
    SlyDeal,
)
from models.cards.money import MoneyCard
from models.cards.property import Color, SingleColorProperty
from models.cards.rent import RentCard
from models.game.commands import (
    DiscardCards,
    EndTurn,
    PassJustSayNo,
    PayDebt,
    PlayJustSayNo,
    PlayMoneyFromHand,
    PlayPassGo,
    PlayRent,
    PlaySlyDeal,
)
from models.game.commands.rent import rent_m_due_for_color
from models.game.game import Game
from models.game.legal_moves import legal_moves
from models.game.pending import PaymentDue


def _add_partial_red_set(game: Game, player_idx: int, count: int) -> None:
    player = game.players[player_idx]
    for _ in range(count):
        player.add_property_to_board(
            SingleColorProperty(Color.RED, "Kentucky Avenue", [2, 3, 6], 3),
            Color.RED,
        )


class LegalMovesTests(unittest.TestCase):
    def test_main_phase_includes_end_turn_and_money_play(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1), MoneyCard(2)]
        game.plays_this_turn = 0

        moves = game.legal_moves()
        types = {type(m) for m in moves}

        self.assertIn(EndTurn, types)
        self.assertIn(PlayMoneyFromHand, types)
        self.assertEqual(len([m for m in moves if isinstance(m, PlayMoneyFromHand)]), 2)

    def test_main_phase_pass_go(self) -> None:
        game = Game()
        game.players[0].hand = [PassGo()]
        moves = game.legal_moves()
        self.assertEqual([PlayPassGo(0)], [m for m in moves if isinstance(m, PlayPassGo)])

    def test_over_hand_limit_only_discard_combinations(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 8
        moves = game.legal_moves()
        self.assertTrue(all(isinstance(m, DiscardCards) for m in moves))
        self.assertEqual(len(moves), 8)
        for move in moves:
            self.assertEqual(len(move.hand_indices), 1)

    def test_discard_enumerate_matches_legal_moves(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 10
        enumerated = DiscardCards.enumerate(game)
        legal = [m for m in game.legal_moves() if isinstance(m, DiscardCards)]
        self.assertEqual(len(enumerated), 120)
        self.assertEqual(len(legal), 120)

    def test_rent_targets_creditor_board_color_and_opponent(self) -> None:
        game = Game()
        _add_partial_red_set(game, 0, 2)
        game.players[0].hand = [RentCard(Color.RED, Color.YELLOW)]
        game.players[1].hand = []

        moves = [m for m in game.legal_moves() if isinstance(m, PlayRent)]
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].victim_idx, 1)
        self.assertEqual(moves[0].charged_color, Color.RED)
        self.assertEqual(rent_m_due_for_color(game.players[0], Color.RED), 3)

    def test_rent_skips_zero_due_color(self) -> None:
        game = Game()
        game.players[0].hand = [RentCard(Color.RED, Color.YELLOW)]
        moves = [m for m in game.legal_moves() if isinstance(m, PlayRent)]
        self.assertEqual(moves, [])

    def test_sly_deal_enumerates_steal_targets(self) -> None:
        game = Game()
        game.players[0].hand = [SlyDeal()]
        victim = game.players[1]
        victim.add_property_to_board(
            SingleColorProperty(Color.RED, "Kentucky Avenue", [2, 3, 6], 3),
            Color.RED,
        )

        moves = [m for m in game.legal_moves() if isinstance(m, PlaySlyDeal)]
        self.assertEqual(len(moves), 1)
        self.assertEqual(
            moves[0],
            PlaySlyDeal(0, 1, 0, 0, Color.RED),
        )

    def test_payment_due_includes_pay_and_just_say_no(self) -> None:
        game = Game()
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=3)
        game.acting_player_idx = 1
        game.players[1].money_pile = [MoneyCard(3)]
        game.players[1].hand = [
            ActionCard(ActionCardType.JUST_SAY_NO, 4),
        ]

        moves = game.legal_moves()
        types = {type(m) for m in moves}

        self.assertIn(PayDebt, types)
        self.assertIn(PlayJustSayNo, types)
        self.assertNotIn(PassJustSayNo, types)
        pay_moves = [m for m in moves if isinstance(m, PayDebt)]
        self.assertIn(PayDebt([0], []), pay_moves)

    def test_payment_jsn_chain_creditor_cannot_pay(self) -> None:
        from models.game.pending import JustSayNoNegotiation

        game = Game()
        game.pending = PaymentDue(
            creditor_idx=0,
            debtor_idx=1,
            amount_m=3,
            jsn=JustSayNoNegotiation(
                defender_idx=1,
                actor_idx=0,
                responder="actor",
                chain_started=True,
            ),
        )
        game.acting_player_idx = 0
        game.players[0].hand = [ActionCard(ActionCardType.JUST_SAY_NO, 4)]

        moves = game.legal_moves()
        self.assertFalse(any(isinstance(m, PayDebt) for m in moves))
        self.assertIn(PassJustSayNo(), moves)

    def test_debt_collector_opens_payment_moves_for_debtor(self) -> None:
        game = Game()
        game.players[0].hand = [DebtCollector()]
        moves = game.legal_moves()
        debt_collector = [
            m for m in moves if m.__class__.__name__ == "PlayDebtCollector"
        ]
        self.assertEqual(len(debt_collector), 1)

    def test_acting_player_must_match_for_main_phase(self) -> None:
        game = Game()
        game.acting_player_idx = 1
        game.players[0].hand = [MoneyCard(1)]
        self.assertEqual(game.legal_moves(), [])

    def test_every_legal_move_passes_validate(self) -> None:
        game = Game()
        _add_partial_red_set(game, 0, 2)
        game.players[0].hand = [
            MoneyCard(1),
            RentCard(Color.RED, Color.YELLOW),
            PassGo(),
            SlyDeal(),
        ]
        for move in game.legal_moves():
            move.validate(game)


if __name__ == "__main__":
    unittest.main()
