import unittest

from encoder.encode_hand import encode_hand
from encoder.layout import COLORS, HAND_DIM
from models.cards.money import MoneyCard
from models.cards.property import Color, PropertySet, SingleColorProperty
from models.cards.rent import RentCard


class EncodeHandTests(unittest.TestCase):
    def test_hand_money_only_counts_money_cards(self) -> None:
        hand = [MoneyCard(1), MoneyCard(10)]
        encoded = encode_hand(hand, [])
        self.assertEqual(len(encoded), HAND_DIM)
        self.assertAlmostEqual(encoded[0], 1 / 7)
        self.assertAlmostEqual(encoded[5], 1 / 7)

    def test_max_charge_requires_board_and_rent_card(self) -> None:
        pile = PropertySet(Color.BROWN)
        pile.add(SingleColorProperty(Color.BROWN, "Med", [1, 2], 1))
        hand = [RentCard(Color.BROWN, Color.LIGHT_BLUE)]
        encoded = encode_hand(hand, [pile])
        charge_start = 6 + len(COLORS)
        brown_charge = encoded[charge_start + COLORS.index(Color.BROWN)]
        self.assertAlmostEqual(brown_charge, 1 / 15)

    def test_max_charge_zero_without_board_set(self) -> None:
        hand = [RentCard(Color.BROWN, Color.LIGHT_BLUE)]
        encoded = encode_hand(hand, [])
        charge_start = 6 + len(COLORS)
        self.assertEqual(encoded[charge_start : charge_start + len(COLORS)], [0.0] * len(COLORS))


if __name__ == "__main__":
    unittest.main()
