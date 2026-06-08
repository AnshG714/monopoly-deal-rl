from copy import deepcopy
import random
from models.game.game import Game


def _rng_from_state(source: random.Random) -> random.Random:
    rng = random.Random()
    rng.setstate(source.getstate())
    return rng


def determinize(game: Game, rng: random.Random | None = None) -> Game:
    """
    Creates a new game state by sampling a different world for information unknown by the
    acting player.

    When ``rng`` is supplied, it is the only object whose state is consumed.
    The root ``game`` must not be mutated just because a search is thinking.
    """

    new_game = deepcopy(game)
    if rng is None:
        shuffle_rng = _rng_from_state(game._rng)
    else:
        shuffle_rng = rng
        new_game._rng = random.Random(rng.randrange(2**63))

    deck = new_game.deck
    acting_player_idx = new_game.acting_player_idx
    other_player_idx = 1 - acting_player_idx  # This is only for a 2-player game.
    other_player_hand = new_game.players[other_player_idx].hand
    other_player_hand_size = len(other_player_hand)

    # combine the "unknowns"
    unknown_cards = other_player_hand + deck
    shuffle_rng.shuffle(unknown_cards)

    # Straight replace.
    new_game.players[other_player_idx].hand = unknown_cards[:other_player_hand_size]
    new_game.deck = unknown_cards[other_player_hand_size:]
    return new_game
