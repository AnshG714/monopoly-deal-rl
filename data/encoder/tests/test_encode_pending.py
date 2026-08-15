import unittest

from data.encoder.state_encoder.encode_pending import encode_pending
from data.encoder.state_encoder.layout import PENDING_DIM, PENDING_KINDS
from models.cards.property import Color, PropertySet, WildColorProperty
from models.game.pending import (
    JustSayNoNegotiation,
    PaymentDue,
    SlyDealPending,
    SlyDealStealIntent,
)


class EncodePendingTests(unittest.TestCase):
    def test_none_pending_is_zeros(self) -> None:
        encoded = encode_pending(None, 0, [], [])
        self.assertEqual(encoded, [0.0] * PENDING_DIM)

    def test_payment_due_debtor_flag(self) -> None:
        pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=7)
        encoded = encode_pending(pending, viewer_idx=1, viewer_piles=[], opponent_piles=[])
        self.assertEqual(encoded[PENDING_KINDS.index("PaymentDue")], 1.0)
        self.assertAlmostEqual(encoded[4], 7 / 20)
        self.assertEqual(encoded[30], 1.0)

    def test_sly_deal_take_wild_flag(self) -> None:
        victim_pile = PropertySet(Color.RED)
        victim_pile.add(WildColorProperty())
        pending = SlyDealPending(
            actor_idx=0,
            steal=SlyDealStealIntent(
                victim_idx=1,
                target_set_idx=0,
                target_card_idx=0,
                into_color=Color.RED,
            ),
            jsn=JustSayNoNegotiation.open_negotiation(defender_idx=1, actor_idx=0),
        )
        encoded = encode_pending(
            pending,
            viewer_idx=1,
            viewer_piles=[victim_pile],
            opponent_piles=[],
        )
        self.assertEqual(encoded[PENDING_KINDS.index("SlyDealPending")], 1.0)
        self.assertEqual(encoded[27], 1.0)
        self.assertEqual(encoded[33], 0.0)


if __name__ == "__main__":
    unittest.main()
