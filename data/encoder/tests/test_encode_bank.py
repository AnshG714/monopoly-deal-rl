import unittest

from encoder.encode_bank import encode_bank
from encoder.layout import BANK_DIM, BANK_MAX_COUNTS
from models.cards.action import JustSayNo
from models.cards.money import MoneyCard


class EncodeBankTests(unittest.TestCase):
    def test_counts_money_by_denomination(self) -> None:
        viewer = [MoneyCard(1), MoneyCard(1), MoneyCard(5)]
        opponent = [MoneyCard(10)]
        encoded = encode_bank(viewer, opponent)

        self.assertEqual(len(encoded), BANK_DIM)
        self.assertAlmostEqual(encoded[0], 2 / BANK_MAX_COUNTS[1])
        self.assertAlmostEqual(encoded[4], 1 / BANK_MAX_COUNTS[5])
        self.assertAlmostEqual(encoded[5], 0.0)
        self.assertAlmostEqual(encoded[6 + 5], 1 / BANK_MAX_COUNTS[10])

    def test_counts_any_bankable_face_value(self) -> None:
        bank = [JustSayNo()]
        encoded = encode_bank(bank, [])
        self.assertAlmostEqual(encoded[3], 1 / BANK_MAX_COUNTS[4])


if __name__ == "__main__":
    unittest.main()
