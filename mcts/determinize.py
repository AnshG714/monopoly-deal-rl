from copy import deepcopy
import random
from models.game.game import Game


def determinize(game: Game) -> Game:
    """
    Creates a new game state by sampling a different world for information unknown by the
    acting player.
    """

    new_game = deepcopy(game)
    deck = new_game.deck
    acting_player_idx = new_game.acting_player_idx
    other_player_idx = 1 - acting_player_idx  # This is only for a 2-player game.
    other_player_hand = new_game.players[other_player_idx].hand
    other_player_hand_size = len(other_player_hand)

    # combine the "unknowns"
    unknown_cards = other_player_hand + deck
    shuffle_rng = random.Random(game._rng.random())
    shuffle_rng.shuffle(unknown_cards)

    # Straight replace.
    new_game.players[other_player_idx].hand = unknown_cards[:other_player_hand_size]
    new_game.deck = unknown_cards[other_player_hand_size:]
    return new_game
