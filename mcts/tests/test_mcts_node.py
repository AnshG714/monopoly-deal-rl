from __future__ import annotations

import unittest

from models.game.commands import DiscardCards, EndTurn, PayDebt
from mcts.node import ISMCTSNode


class CommandHashEqualityTests(unittest.TestCase):
    def test_pay_debt_ignores_money_index_order(self) -> None:
        a = PayDebt([1, 0], [])
        b = PayDebt([0, 1], [])
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_discard_cards_ignores_hand_index_order(self) -> None:
        a = DiscardCards([2, 0, 1])
        b = DiscardCards([0, 1, 2])
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))


class ISMCTSNodeIdentityTests(unittest.TestCase):
    def test_unexpanded_treats_reordered_pay_debt_as_expanded(self) -> None:
        node = ISMCTSNode()
        existing = PayDebt([0, 1], [])
        node.children.append(ISMCTSNode(existing, node))

        candidate = PayDebt([1, 0], [])
        unexpanded = node.get_unexpanded_moves([candidate, PayDebt([2], [])])

        self.assertEqual(unexpanded, [PayDebt([2], [])])

    def test_unexpanded_treats_reordered_discard_as_expanded(self) -> None:
        node = ISMCTSNode()
        existing = DiscardCards([0, 1])
        node.children.append(ISMCTSNode(existing, node))

        candidate = DiscardCards([1, 0])
        unexpanded = node.get_unexpanded_moves([candidate, DiscardCards([2, 3])])

        self.assertEqual(unexpanded, [DiscardCards([2, 3])])

    def test_legal_children_match_by_command_equality(self) -> None:
        node = ISMCTSNode()
        child_move = PayDebt([0], [])
        node.children.append(ISMCTSNode(child_move, node))

        legal = [PayDebt([0], []), EndTurn()]
        legal_children = node.get_legal_children(legal)

        self.assertEqual(len(legal_children), 1)
        self.assertIs(legal_children[0].move, child_move)

    def test_availability_counts_use_command_keys(self) -> None:
        node = ISMCTSNode()
        child = ISMCTSNode(PayDebt([0], []), node)
        child.visits = 1
        child.wins = 0
        node.children.append(child)

        reordered = PayDebt([0], [])
        node.choose_child_uct([reordered])

        self.assertEqual(node.availability_counts[reordered], 1)


if __name__ == "__main__":
    unittest.main()
