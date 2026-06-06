from __future__ import annotations

import unittest

from models.cards.action import DealBreaker, Hotel, House
from models.cards.property import Color, SingleColorProperty
from models.game.game import Game
from models.game.pending import PaymentDue
from models.game.commands.rent import rent_m_due_for_color


def _add_complete_red_set(game: Game, player_idx: int) -> None:
    player = game.players[player_idx]
    player.add_property_to_board(
        SingleColorProperty(Color.RED, "Kentucky Avenue", [2, 3, 6], 3), Color.RED
    )
    player.add_property_to_board(
        SingleColorProperty(Color.RED, "Indiana Avenue", [2, 3, 6], 3), Color.RED
    )
    player.add_property_to_board(
        SingleColorProperty(Color.RED, "Illinois Avenue", [2, 3, 6], 3), Color.RED
    )


class HouseHotelTests(unittest.TestCase):
    def test_play_house_on_complete_set(self) -> None:
        game = Game()
        _add_complete_red_set(game, 0)
        game.players[0].hand = [House()]

        game.play_house(hand_index=0, target_set_idx=0)

        pile = game.players[0].pile_at(0)
        self.assertTrue(pile.has_house())
        self.assertEqual(game.plays_this_turn, 1)
        self.assertEqual(len(game.players[0].hand), 0)

    def test_hotel_requires_house(self) -> None:
        game = Game()
        _add_complete_red_set(game, 0)
        game.players[0].hand = [Hotel()]

        with self.assertRaises(ValueError):
            game.play_hotel(hand_index=0, target_set_idx=0)

    def test_duplicate_house_is_rejected(self) -> None:
        game = Game()
        _add_complete_red_set(game, 0)
        game.players[0].hand = [House(), House()]

        game.play_house(hand_index=0, target_set_idx=0)
        with self.assertRaises(ValueError):
            game.play_house(hand_index=0, target_set_idx=0)

    def test_rent_includes_house_hotel_bonus(self) -> None:
        game = Game()
        _add_complete_red_set(game, 0)
        pile = game.players[0].pile_at(0)

        self.assertEqual(rent_m_due_for_color(game.players[0], Color.RED), 6)
        pile.attach_house(House())
        self.assertEqual(rent_m_due_for_color(game.players[0], Color.RED), 9)
        pile.attach_hotel(Hotel())
        self.assertEqual(rent_m_due_for_color(game.players[0], Color.RED), 13)

    def test_breaking_complete_set_for_payment_banks_buildings(self) -> None:
        game = Game()
        _add_complete_red_set(game, 0)
        pile = game.players[0].pile_at(0)
        pile.attach_house(House())
        pile.attach_hotel(Hotel())

        game.current_player_idx = 1
        game.pending = PaymentDue(creditor_idx=1, debtor_idx=0, amount_m=1)
        game.acting_player_idx = 0

        game.pay_debt(money_pile_indices=[], property_card_indices=[(0, 0)])

        debtor_pile = game.players[0].pile_at(0)
        self.assertFalse(debtor_pile.has_house())
        self.assertFalse(debtor_pile.has_hotel())
        self.assertEqual(len(game.players[0].money_pile), 2)
        self.assertTrue(
            any(isinstance(card, House) for card in game.players[0].money_pile)
        )
        self.assertTrue(
            any(isinstance(card, Hotel) for card in game.players[0].money_pile)
        )

    def test_deal_breaker_transfers_set_with_buildings_attached(self) -> None:
        game = Game()
        _add_complete_red_set(game, 1)
        victim_pile = game.players[1].pile_at(0)
        victim_pile.attach_house(House())
        victim_pile.attach_hotel(Hotel())
        game.players[0].hand = [DealBreaker()]

        game.play_deal_breaker(hand_index=0, victim_idx=1, victim_set_idx=0)
        game.pass_just_say_no()

        actor_pile = game.players[0].pile_at(0)
        self.assertTrue(actor_pile.has_house())
        self.assertTrue(actor_pile.has_hotel())
        self.assertEqual(len(game.players[1].property_sets), 0)


if __name__ == "__main__":
    unittest.main()
