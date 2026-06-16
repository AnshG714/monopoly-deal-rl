from __future__ import annotations

import unittest

from models.cards.action import House
from models.cards.property import (
    Color,
    MultiColorProperty,
    SingleColorProperty,
    WildColorProperty,
)
from models.game.commands.move_wild_property import MoveWildProperty
from models.game.game import Game

_RENT_PINK = [1, 2, 4]
_RENT_ORANGE = [1, 3, 5]


def _pink_orange_wild() -> MultiColorProperty:
    return MultiColorProperty(Color.PINK, _RENT_PINK, Color.ORANGE, _RENT_ORANGE, 2)


def _orange(name: str) -> SingleColorProperty:
    return SingleColorProperty(Color.ORANGE, name, _RENT_ORANGE, 3)


def _pink(name: str) -> SingleColorProperty:
    return SingleColorProperty(Color.PINK, name, _RENT_PINK, 2)


class MoveWildPropertyTests(unittest.TestCase):
    def test_move_dual_wild_completes_destination_set(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(_orange("A"), Color.ORANGE)
        player.add_property_to_board(_orange("B"), Color.ORANGE)
        player.add_property_to_board(_pink_orange_wild(), Color.PINK)

        game.apply(
            MoveWildProperty(from_set_idx=1, card_idx=0, into_color=Color.ORANGE)
        )

        orange_pile = next(p for p in player.property_sets if p.color == Color.ORANGE)
        self.assertTrue(orange_pile.is_complete())
        self.assertEqual(len(orange_pile.cards), 3)
        self.assertEqual(game.plays_this_turn, 1)

    def test_move_off_complete_set_banks_buildings(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(_pink("A"), Color.PINK)
        player.add_property_to_board(_pink("B"), Color.PINK)
        player.add_property_to_board(_pink_orange_wild(), Color.PINK)
        pink_pile = player.pile_at(0)
        pink_pile.attach_house(House())

        game.apply(
            MoveWildProperty(from_set_idx=0, card_idx=2, into_color=Color.ORANGE)
        )

        pink_pile = player.pile_at(0)
        self.assertFalse(pink_pile.is_complete())
        self.assertFalse(pink_pile.has_house())
        self.assertEqual(len(player.money_pile), 1)
        self.assertEqual(player.money_pile[0].value, 3)

    def test_rejects_move_onto_complete_destination(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(_orange("A"), Color.ORANGE)
        player.add_property_to_board(_orange("B"), Color.ORANGE)
        player.add_property_to_board(_orange("C"), Color.ORANGE)
        player.add_property_to_board(_pink_orange_wild(), Color.PINK)

        with self.assertRaises(ValueError):
            game.apply(
                MoveWildProperty(from_set_idx=1, card_idx=0, into_color=Color.ORANGE)
            )

    def test_rejects_non_wild_card(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(_pink("A"), Color.PINK)
        player.add_property_to_board(_orange("B"), Color.ORANGE)

        with self.assertRaises(TypeError):
            game.apply(
                MoveWildProperty(from_set_idx=0, card_idx=0, into_color=Color.ORANGE)
            )

    def test_ten_color_wild_can_move_to_any_incomplete_set(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(WildColorProperty(), Color.RED)
        player.add_property_to_board(
            SingleColorProperty(Color.GREEN, "Pacific", [2, 4, 7], 4), Color.GREEN
        )

        game.apply(MoveWildProperty(from_set_idx=0, card_idx=0, into_color=Color.GREEN))

        green_pile = player.pile_at(0)
        self.assertEqual(green_pile.color, Color.GREEN)
        self.assertEqual(len(green_pile.cards), 2)
        self.assertNotIn(Color.RED, [p.color for p in player.property_sets])

    def test_appears_in_legal_moves(self) -> None:
        game = Game()
        player = game.players[0]
        player.add_property_to_board(_orange("A"), Color.ORANGE)
        player.add_property_to_board(_orange("B"), Color.ORANGE)
        player.add_property_to_board(_pink_orange_wild(), Color.PINK)

        moves = game.legal_moves()
        self.assertIn(MoveWildProperty(1, 0, Color.ORANGE), moves)


if __name__ == "__main__":
    unittest.main()
