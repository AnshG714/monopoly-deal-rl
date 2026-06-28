import unittest

from encoder.encode_properties import encode_properties
from encoder.layout import PROPERTIES_DIM
from models.cards.property import Color, PropertySet, SingleColorProperty


class EncodePropertiesTests(unittest.TestCase):
    def test_empty_board_is_zeros(self) -> None:
        encoded = encode_properties([], [])
        self.assertEqual(len(encoded), PROPERTIES_DIM)
        self.assertEqual(encoded, [0.0] * PROPERTIES_DIM)

    def test_current_rentable_matches_engine(self) -> None:
        pile = PropertySet(Color.BROWN)
        pile.add(
            SingleColorProperty(Color.BROWN, "Mediterranean Avenue", [1, 2], 1)
        )
        encoded = encode_properties([pile], [])
        from encoder.layout import COLORS

        idx = COLORS.index(Color.BROWN) * 7
        self.assertAlmostEqual(encoded[idx + 1], 1 / 15)


if __name__ == "__main__":
    unittest.main()
