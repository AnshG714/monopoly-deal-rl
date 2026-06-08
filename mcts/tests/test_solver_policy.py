from __future__ import annotations

import random
import unittest

from models.cards.action import ForcedDeal, ItsMyBirthday
from models.cards.money import MoneyCard
from models.cards.property import Color, SingleColorProperty, CARDS_IN_SET_FOR_COLOR
from models.cards.rent import RentCard
from models.game.commands import PlayItsMyBirthday, PlayMoneyFromHand, PlayRent
from models.game.game import Game
from mcts.solver import ISMCTSSolver
from rollout import choose_move, is_dominated_money_play


def _setup(
    hand,
    *,
    properties: list[tuple[Color, int]] | None = None,
    opponent_bank: list[int] | None = None,
) -> Game:
    game = Game(rng=random.Random(0))
    game.current_player_idx = 0
    game.acting_player_idx = 0
    game.pending = None
    game.plays_this_turn = 0
    player = game.players[0]
    player.hand = list(hand)
    player.property_sets = []
    for color, count in properties or []:
        rents = list(range(1, CARDS_IN_SET_FOR_COLOR[color] + 1))
        for _ in range(count):
            player.add_property_to_board(
                SingleColorProperty(color, "X", rents, 3),
                color,
            )
    opponent = game.players[1]
    opponent.money_pile = [MoneyCard(value) for value in opponent_bank or []]
    return game


class MCTSPolicyRegressionTests(unittest.TestCase):
    def test_rollout_and_mcts_charge_birthday_when_collectible(self) -> None:
        game = _setup(
            [ItsMyBirthday()],
            properties=[(Color.RED, 1)],
            opponent_bank=[1, 1],
        )
        rollout_move = choose_move(game)
        mcts_move = ISMCTSSolver(
            iterations=200,
            rng=random.Random(0),
        ).search(game)

        self.assertIsInstance(rollout_move, PlayItsMyBirthday)
        self.assertIsInstance(mcts_move, PlayItsMyBirthday)

    def test_rollout_and_mcts_charge_rent_when_collectible(self) -> None:
        game = _setup(
            [RentCard(Color.RED, Color.YELLOW)],
            properties=[(Color.RED, 2)],
            opponent_bank=[3],
        )
        rollout_move = choose_move(game)
        mcts_move = ISMCTSSolver(
            iterations=200,
            rng=random.Random(0),
        ).search(game)

        self.assertIsInstance(rollout_move, PlayRent)
        self.assertIsInstance(mcts_move, PlayRent)

    def test_mcts_may_bank_birthday_when_debtor_has_no_assets(self) -> None:
        game = _setup([ItsMyBirthday()], properties=[(Color.RED, 1)])
        move = ISMCTSSolver(
            iterations=200,
            rng=random.Random(0),
        ).search(game)

        self.assertIsInstance(move, PlayMoneyFromHand)

    def test_mcts_search_does_not_mutate_root_rng_state(self) -> None:
        game = _setup(
            [ItsMyBirthday()],
            properties=[(Color.RED, 1)],
            opponent_bank=[1, 1],
        )
        before = game._rng.getstate()

        ISMCTSSolver(
            iterations=5,
            rng=random.Random(0),
        ).search(game)

        self.assertEqual(game._rng.getstate(), before)

    def test_dominated_money_play_when_charge_is_legal(self) -> None:
        game = _setup([ItsMyBirthday()], properties=[(Color.RED, 1)])
        bank = PlayMoneyFromHand(0)
        self.assertTrue(is_dominated_money_play(game, bank))

    def test_forced_deal_not_dominated_as_money(self) -> None:
        game = _setup([ForcedDeal()], properties=[(Color.RED, 1)])
        bank = PlayMoneyFromHand(0)
        self.assertFalse(is_dominated_money_play(game, bank))
        self.assertIsInstance(choose_move(game), PlayMoneyFromHand)


if __name__ == "__main__":
    unittest.main()
