from __future__ import annotations

import unittest

from models.game.combinatorics import (
    combinations_greater_than_amount,
    combinations_of_indices,
)


class CombinatoricsTests(unittest.TestCase):
    def test_combinations_of_indices_choose_two_of_four(self) -> None:
        self.assertEqual(
            combinations_of_indices(4, 2),
            [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]],
        )

    def test_combinations_greater_than_amount_single_bill(self) -> None:
        self.assertEqual(combinations_greater_than_amount([5], 3), [[0]])
        self.assertEqual(combinations_greater_than_amount([5], 5), [[0]])

    def test_combinations_greater_than_amount_no_voluntary_overpay(self) -> None:
        # 5M covers debt; 4M extra property must not appear on the same subset.
        self.assertEqual(combinations_greater_than_amount([5, 4], 5), [[0]])

    def test_combinations_greater_than_amount_multiple_minimal_ways(self) -> None:
        self.assertEqual(
            combinations_greater_than_amount([5, 2, 1], 3),
            [[0], [1, 2]],
        )

    def test_combinations_greater_than_amount_need_multiple_cards(self) -> None:
        self.assertEqual(combinations_greater_than_amount([3, 3], 5), [[0, 1]])

    def test_combinations_greater_than_amount_insufficient_pool(self) -> None:
        self.assertEqual(combinations_greater_than_amount([3, 3], 10), [])

    def test_combinations_greater_than_amount_zero_amount(self) -> None:
        self.assertEqual(combinations_greater_than_amount([2, 1], 0), [[]])


class PayDebtEnumerationTests(unittest.TestCase):
    def test_pay_debt_excludes_voluntary_overpay(self) -> None:
        from models.cards.money import MoneyCard
        from models.cards.property import Color, SingleColorProperty
        from models.game.commands import PayDebt
        from models.game.game import Game
        from models.game.legal_moves import legal_moves
        from models.game.pending import PaymentDue

        game = Game()
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=3)
        game.acting_player_idx = 1
        debtor = game.players[1]
        debtor.money_pile = [MoneyCard(3)]
        # 2M property alone cannot clear 3M; only 3M money should be offered.
        debtor.add_property_to_board(
            SingleColorProperty(Color.RED, "Kentucky Avenue", [1, 2, 3], 2),
            Color.RED,
        )

        pay_moves = [m for m in legal_moves(game) if isinstance(m, PayDebt)]
        self.assertEqual(pay_moves, [PayDebt([0], [])])
