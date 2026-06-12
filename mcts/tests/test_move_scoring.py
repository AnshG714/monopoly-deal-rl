from __future__ import annotations

import random
import unittest

from mcts.move_scoring import select_interrupt_moves, select_top_moves, score_move
from models.cards.action import JustSayNo, PassGo
from models.cards.money import MoneyCard
from models.cards.property import (
    CARDS_IN_SET_FOR_COLOR,
    Color,
    SingleColorProperty,
    WildColorProperty,
)
from models.cards.rent import RentCard
from models.game.commands import (
    EndTurn,
    PayDebt,
    PlayJustSayNo,
    PlayMoneyFromHand,
    PlayPassGo,
    PlayPropertyFromHand,
    PlayRent,
)
from models.game.game import Game
from models.game.pending import PaymentDue


def _rents(color: Color) -> list[int]:
    return list(range(1, CARDS_IN_SET_FOR_COLOR[color] + 1))


class MoveScoringTests(unittest.TestCase):
    def test_completing_property_color_scores_above_non_completing_color(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 0
        game.players[0].hand = [WildColorProperty()]
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "B", _rents(Color.RED), 3),
            Color.RED,
        )
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "C", _rents(Color.RED), 3),
            Color.RED,
        )

        completes_red = PlayPropertyFromHand(0, Color.RED)
        starts_yellow = PlayPropertyFromHand(0, Color.YELLOW)

        self.assertGreater(
            score_move(game, completes_red, root_player_idx=0),
            score_move(game, starts_yellow, root_player_idx=0),
        )

    def test_collectible_rent_scores_above_banking_rent_card(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 0
        game.players[0].hand = [RentCard(Color.RED, Color.YELLOW)]
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "A", _rents(Color.RED), 3),
            Color.RED,
        )
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "B", _rents(Color.RED), 3),
            Color.RED,
        )
        game.players[1].money_pile = [MoneyCard(3)]

        rent = PlayRent(0, 1, Color.RED)
        bank = PlayMoneyFromHand(0)

        self.assertGreater(
            score_move(game, rent, root_player_idx=0),
            score_move(game, bank, root_player_idx=0),
        )

    def test_bucketed_pruning_preserves_draw_move(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 0
        game.players[0].hand = [WildColorProperty(), PassGo()]
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "A", _rents(Color.RED), 3),
            Color.RED,
        )
        game.players[0].add_property_to_board(
            SingleColorProperty(Color.RED, "B", _rents(Color.RED), 3),
            Color.RED,
        )
        moves = [
            PlayPropertyFromHand(0, Color.RED),
            PlayPropertyFromHand(0, Color.YELLOW),
            PlayPropertyFromHand(0, Color.GREEN),
            PlayPassGo(1),
        ]

        selected = select_top_moves(
            game,
            moves,
            root_player_idx=0,
            max_moves=2,
            heuristic_move=PlayPropertyFromHand(0, Color.RED),
            strategy="bucketed",
        )

        self.assertIn(PlayPassGo(1), selected)

    def test_pruning_keeps_opponent_best_moves_on_opponent_turn(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 1
        game.acting_player_idx = 1
        game.players[0].money_pile = [MoneyCard(3)]
        game.players[1].hand = [RentCard(Color.RED, Color.YELLOW), MoneyCard(5)]
        game.players[1].add_property_to_board(
            SingleColorProperty(Color.RED, "A", _rents(Color.RED), 3),
            Color.RED,
        )
        game.players[1].add_property_to_board(
            SingleColorProperty(Color.RED, "B", _rents(Color.RED), 3),
            Color.RED,
        )
        rent = PlayRent(0, 0, Color.RED)
        moves = [
            EndTurn(),
            PlayMoneyFromHand(0),
            PlayMoneyFromHand(1),
            rent,
        ]

        selected = select_top_moves(
            game,
            moves,
            root_player_idx=0,
            max_moves=2,
            heuristic_move=EndTurn(),
            strategy="global",
        )

        self.assertIn(rent, selected)

    def test_interrupt_pruning_keeps_multiple_scored_payment_options(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 1
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=4)
        game.players[1].money_pile = [
            MoneyCard(1),
            MoneyCard(2),
            MoneyCard(3),
            MoneyCard(4),
        ]
        moves = game.legal_moves()

        selected = select_interrupt_moves(
            game,
            moves,
            root_player_idx=1,
            max_moves=3,
        )

        self.assertEqual(len(selected), 3)
        self.assertGreater(len([move for move in selected if isinstance(move, PayDebt)]), 1)

    def test_just_say_no_scores_above_payment_for_large_collectible_debt(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 1
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=5)
        game.players[1].hand = [JustSayNo()]
        game.players[1].money_pile = [MoneyCard(5)]

        self.assertGreater(
            score_move(game, PlayJustSayNo(0), root_player_idx=1),
            score_move(game, PayDebt([0]), root_player_idx=1),
        )

    def test_payment_scoring_preserves_complete_sets_before_cash(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 1
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=3)
        debtor = game.players[1]
        debtor.money_pile = [MoneyCard(3)]
        debtor.add_property_to_board(
            SingleColorProperty(Color.BROWN, "A", _rents(Color.BROWN), 3),
            Color.BROWN,
        )
        debtor.add_property_to_board(
            SingleColorProperty(Color.BROWN, "B", _rents(Color.BROWN), 3),
            Color.BROWN,
        )

        self.assertGreater(
            score_move(game, PayDebt([0]), root_player_idx=1),
            score_move(game, PayDebt([], [(0, 0)]), root_player_idx=1),
        )

    def test_payment_scoring_avoids_completing_creditor_set(self) -> None:
        game = Game(rng=random.Random(0))
        game.current_player_idx = 0
        game.acting_player_idx = 1
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=3)
        creditor = game.players[0]
        debtor = game.players[1]
        creditor.add_property_to_board(
            SingleColorProperty(Color.BLUE, "Boardwalk", _rents(Color.BLUE), 4),
            Color.BLUE,
        )
        debtor.add_property_to_board(
            SingleColorProperty(Color.BLUE, "Park Place", _rents(Color.BLUE), 3),
            Color.BLUE,
        )
        debtor.add_property_to_board(
            SingleColorProperty(Color.RED, "Kentucky", _rents(Color.RED), 3),
            Color.RED,
        )

        self.assertGreater(
            score_move(game, PayDebt([], [(1, 0)]), root_player_idx=1),
            score_move(game, PayDebt([], [(0, 0)]), root_player_idx=1),
        )


if __name__ == "__main__":
    unittest.main()
