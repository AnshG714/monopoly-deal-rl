"""Heuristic move selection for rollout playouts."""

from __future__ import annotations

from models.cards.action import ActionCard, ActionCardType
from models.cards.base import Card, CardType
from models.cards.money import MoneyCard
from models.cards.property import (
    CARDS_IN_SET_FOR_COLOR,
    Color,
    MultiColorProperty,
    PropertyCard,
    PropertySet,
    SingleColorProperty,
    WildColorProperty,
)
from models.cards.rent import RentCard, WildRentCard
from models.game.commands import (
    DiscardCards,
    EndTurn,
    GameCommand,
    PassJustSayNo,
    PayDebt,
    PlayDealBreaker,
    PlayDebtCollector,
    PlayDoubleRent,
    PlayForcedDeal,
    PlayHotel,
    PlayHouse,
    PlayItsMyBirthday,
    PlayJustSayNo,
    PlayMoneyFromHand,
    PlayPassGo,
    PlayPropertyFromHand,
    PlayRent,
    PlaySlyDeal,
    MoveWildProperty,
)
from models.game.commands.debt_collector import DEBT_COLLECTOR_PAYMENT_M
from models.game.commands.its_my_birthday import BIRTHDAY_GIFT_M
from models.game.commands.rent import rent_m_due_for_color
from models.game.game import Game
from models.game.pending import (
    DealBreakerPending,
    ForcedDealPending,
    PaymentDue,
    SlyDealPending,
)
from models.player import Player
from rollout.jsn import count_jsns, side_wins_if_plays_jsn

# card.value is in millions (engine units). Scale only in additive heuristic scores.
SCORE_PER_M = 100


def _face_value_score(card: Card) -> int:
    return card.value * SCORE_PER_M


def choose_move(game: Game) -> GameCommand:
    """Pick one legal move using rollout_strategy.md heuristics."""
    pending = game.pending
    if isinstance(pending, PaymentDue):
        return _choose_payment_fast(game, pending)

    moves = game.legal_moves()
    if not moves:
        raise ValueError("No legal moves found")

    # Engine exposes one branch at a time — match that before main-phase priorities.
    if all(isinstance(m, DiscardCards) for m in moves):
        return _choose_discard(game, [m for m in moves if isinstance(m, DiscardCards)])

    if isinstance(pending, (SlyDealPending, ForcedDealPending, DealBreakerPending)):
        return _choose_defend_steal(game, moves, pending)

    return _choose_main_phase(game, moves)


def dominated_money_hand_indices(game: Game) -> set[int]:
    """Hand indices where banking is dominated by a charge/action on the same card."""
    dominated: set[int] = set()
    for move in game.legal_moves():
        if isinstance(move, PlayItsMyBirthday):
            dominated.add(move.hand_index)
        elif isinstance(move, PlayDebtCollector):
            dominated.add(move.hand_index)
        elif isinstance(move, PlayRent):
            dominated.add(move.hand_index)
        elif isinstance(move, PlayDoubleRent):
            dominated.add(move.double_rent_hand_index)
            dominated.add(move.rent_hand_index)
    return dominated


def is_dominated_money_play(game: Game, move: GameCommand) -> bool:
    if not isinstance(move, PlayMoneyFromHand):
        return False
    return move.hand_index in dominated_money_hand_indices(game)


def _choose_main_phase(game: Game, moves: list[GameCommand]) -> GameCommand:
    # Walk priorities 1→5; first tier with a matching legal move wins.
    for picker in (
        _pick_priority_1,
        _pick_priority_2,
        _pick_priority_3,
        _pick_priority_4,
        _pick_priority_5,
    ):
        chosen = picker(game, moves)
        if chosen is not None:
            return chosen
    # Nothing useful left — hand back to the engine's turn advance + draw-2.
    end_turn = _first_of_type(moves, EndTurn)
    if end_turn is not None:
        return end_turn
    return moves[0]


def _pick_priority_1(game: Game, moves: list[GameCommand]) -> GameCommand | None:
    """Win condition first: complete a set by any means available."""
    # Only steal a full set if the victim cannot JSN-block us.
    deal_breakers = [
        m
        for m in moves
        if isinstance(m, PlayDealBreaker) and _deal_breaker_safe_vs(game, m.victim_idx)
    ]
    if deal_breakers:
        return max(deal_breakers, key=lambda m: _deal_breaker_value(game, m))

    completing_sly = [
        m
        for m in moves
        if isinstance(m, PlaySlyDeal) and _sly_deal_completes_set(game, m)
    ]
    if completing_sly:
        return max(completing_sly, key=lambda m: _stolen_card_value(game, m))

    completing_forced = [
        m
        for m in moves
        if isinstance(m, PlayForcedDeal)
        and _forced_deal_completes_set(game, m)
        and not _forced_deal_breaks_own_set(game, m)
    ]
    if completing_forced:
        return max(completing_forced, key=lambda m: _forced_deal_net_score(m, game))

    completing_props = [
        m
        for m in moves
        if isinstance(m, PlayPropertyFromHand) and _play_property_completes_set(game, m)
    ]
    if completing_props:
        return min(
            completing_props,
            key=lambda m: (m.hand_index, m.into_color.value),
        )

    completing_moves = [
        m
        for m in moves
        if isinstance(m, MoveWildProperty)
        and _move_wild_completes_set(game, m)
        and not _move_wild_breaks_complete_set(game, m)
    ]
    if completing_moves:
        return completing_moves[0]

    return None


def _pick_priority_2(game: Game, moves: list[GameCommand]) -> GameCommand | None:
    """Charge opponents before banking cash — drains their assets and funds ours."""
    charging = [
        m
        for m in moves
        if isinstance(
            m, (PlayRent, PlayDoubleRent, PlayItsMyBirthday, PlayDebtCollector)
        )
    ]
    if not charging:
        return None
    return max(charging, key=lambda m: _charge_amount(game, m))


def _pick_priority_3(game: Game, moves: list[GameCommand]) -> GameCommand | None:
    """Board-building: favor rent-aligned colors, low face value, fixed-color cards."""
    props = [m for m in moves if isinstance(m, PlayPropertyFromHand)]
    if not props:
        return None
    rent_colors = _rent_colors_in_hand(game.current_player())
    # Tie-break order (ascending — lowest tuple wins):
    #  1. Prefer colors we hold a rent card for (can monetize the pile sooner).
    #  2. Play cheapest face-value cards first (keep expensive cards in hand longer).
    #  3. Prefer single-color properties over wilds (wilds stay flexible in hand).
    #  4. Stable tie-break on hand index.
    return min(
        props,
        key=lambda m: (
            0 if m.into_color in rent_colors else 1,
            _hand_card(game, m.hand_index).value,
            0 if _is_single_color_property(_hand_card(game, m.hand_index)) else 1,
            m.hand_index,
        ),
    )


def _pick_priority_4(game: Game, moves: list[GameCommand]) -> GameCommand | None:
    """Bank money so rent debts can be paid without giving up properties."""
    player = game.current_player()
    pass_gos = [m for m in moves if isinstance(m, PlayPassGo)]
    # Spare Pass Go is draw fuel; only dump extras as money here.
    if len(pass_gos) >= 2:
        return pass_gos[0]

    money_plays = [m for m in moves if isinstance(m, PlayMoneyFromHand)]
    plain_money = [
        m for m in money_plays if isinstance(_hand_card(game, m.hand_index), MoneyCard)
    ]
    if plain_money:
        return min(plain_money, key=lambda m: _hand_card(game, m.hand_index).value)

    if player.money_pile:
        return None

    # Last resort: bank actions as money when properties are on the line.
    if player.property_card_count() == 0:
        return None

    action_money = [
        m for m in money_plays if _can_play_as_money(_hand_card(game, m.hand_index))
    ]
    if action_money:
        return min(action_money, key=lambda m: _hand_card(game, m.hand_index).value)

    return None


def _pick_priority_5(game: Game, moves: list[GameCommand]) -> GameCommand | None:
    """Disruption and tempo when set completion isn't on the table."""
    sly = [m for m in moves if isinstance(m, PlaySlyDeal)]
    if sly:
        return max(sly, key=lambda m: _stolen_card_value(game, m))

    hotels = [m for m in moves if isinstance(m, PlayHotel)]
    if hotels:
        return hotels[0]

    houses = [m for m in moves if isinstance(m, PlayHouse)]
    if houses:
        return houses[0]

    forced = [m for m in moves if isinstance(m, PlayForcedDeal)]
    if forced:
        scored = [(m, _forced_deal_net_score(m, game)) for m in forced]
        best = max(scored, key=lambda pair: pair[1])
        # Swaps are symmetric — skip net-negative trades entirely.
        if best[1] > 0:
            return best[0]

    pass_go = [m for m in moves if isinstance(m, PlayPassGo)]
    # Draw cards when nothing else is worth a play slot.
    if pass_go and game._rng.random() < 0.6:
        return pass_go[0]

    return None


def _choose_discard(game: Game, moves: list[DiscardCards]) -> DiscardCards:
    # Score by what we keep; discarded cards re-enter the shuffled deck.
    hand = game.current_player().hand
    return max(
        moves,
        key=lambda m: sum(
            _discard_keep_score(hand[i], game)
            for i in range(len(hand))
            if i not in m.hand_indices
        ),
    )


def _choose_payment(
    game: Game, moves: list[GameCommand], pending: PaymentDue
) -> GameCommand:
    jsn_moves = [m for m in moves if isinstance(m, PlayJustSayNo)]
    if pending.jsn is None:
        # Debtor may open a chain to cancel the charge entirely.
        if jsn_moves and _debtor_should_jsn(game, pending):
            return jsn_moves[0]
    else:
        # Mid-chain: counter only when JSN math favors us, else pass.
        acting = game.acting_player_idx
        defender_idx = pending.debtor_idx
        actor_idx = pending.creditor_idx
        d_jsn = count_jsns(game.players[defender_idx])
        a_jsn = count_jsns(game.players[actor_idx])
        jsn = pending.jsn
        if jsn_moves:
            side = "defender" if acting == defender_idx else "actor"
            if side_wins_if_plays_jsn(
                d_jsn, a_jsn, jsn.responder, jsn.chain_started, side=side
            ):
                return jsn_moves[0]
        pass_moves = [m for m in moves if isinstance(m, PassJustSayNo)]
        if pass_moves:
            return pass_moves[0]

    pay_moves = [m for m in moves if isinstance(m, PayDebt)]
    if not pay_moves:
        return moves[0]
    return _best_pay_debt(game, pay_moves)


def _choose_payment_fast(game: Game, pending: PaymentDue) -> GameCommand:
    """Choose a payment response without enumerating every PayDebt combination."""
    jsn_move = _first_legal_jsn(game)
    if pending.jsn is None:
        if jsn_move is not None and _debtor_should_jsn(game, pending):
            return jsn_move
    else:
        acting = game.acting_player_idx
        defender_idx = pending.debtor_idx
        actor_idx = pending.creditor_idx
        d_jsn = count_jsns(game.players[defender_idx])
        a_jsn = count_jsns(game.players[actor_idx])
        side = "defender" if acting == defender_idx else "actor"
        if jsn_move is not None and side_wins_if_plays_jsn(
            d_jsn,
            a_jsn,
            pending.jsn.responder,
            pending.jsn.chain_started,
            side=side,
        ):
            return jsn_move
        pass_move = PassJustSayNo()
        try:
            pass_move.validate(game)
            return pass_move
        except (ValueError, TypeError, IndexError, RuntimeError):
            pass

    pay_move = _direct_pay_debt(game, pending)
    try:
        pay_move.validate(game)
        return pay_move
    except (ValueError, TypeError, IndexError, RuntimeError):
        # Keep the rollout robust while this optimized path stays conservative.
        return _choose_payment(game, game.legal_moves(), pending)


def _first_legal_jsn(game: Game) -> PlayJustSayNo | None:
    actor = game.players[game.acting_player_idx]
    for hand_index, card in enumerate(actor.hand):
        if (
            isinstance(card, ActionCard)
            and card.action_type == ActionCardType.JUST_SAY_NO
        ):
            move = PlayJustSayNo(hand_index)
            try:
                move.validate(game)
                return move
            except (ValueError, TypeError, IndexError, RuntimeError):
                continue
    return None


def _direct_pay_debt(game: Game, pending: PaymentDue) -> PayDebt:
    debtor = game.players[pending.debtor_idx]
    assets = _payment_assets(game, debtor)
    if not assets:
        return PayDebt([], [])

    if sum(asset["value"] for asset in assets) < pending.amount_m:
        return _pay_debt_from_payment_assets(assets)

    bank_assets = [asset for asset in assets if asset["kind"] == "m"]
    if sum(asset["value"] for asset in bank_assets) >= pending.amount_m:
        return _pay_debt_from_payment_assets(
            _best_payment_subset(bank_assets, pending.amount_m)
        )

    safe_assets = [asset for asset in assets if not asset["breaks_complete_set"]]
    if sum(asset["value"] for asset in safe_assets) >= pending.amount_m:
        return _pay_debt_from_payment_assets(
            _best_payment_subset(safe_assets, pending.amount_m)
        )

    return _pay_debt_from_payment_assets(_best_payment_subset(assets, pending.amount_m))


def _payment_assets(game: Game, debtor: Player) -> list[dict]:
    assets: list[dict] = []
    for money_index, card in enumerate(debtor.money_pile):
        assets.append(
            {
                "kind": "m",
                "index": money_index,
                "value": card.value,
                "progress_lost": 0,
                "property_count": 0,
                "breaks_complete_set": False,
            }
        )
    for set_idx, pile in enumerate(debtor.property_sets):
        for card_idx, card in enumerate(pile.cards):
            progress_lost = _face_value_score(card)
            if _cards_needed(pile) == 1:
                progress_lost += 100
            assets.append(
                {
                    "kind": "p",
                    "index": (set_idx, card_idx),
                    "value": card.value,
                    "progress_lost": progress_lost,
                    "property_count": 1,
                    "breaks_complete_set": pile.is_complete(),
                }
            )
    return assets


def _best_payment_subset(assets: list[dict], amount_m: int) -> list[dict]:
    # Dynamic programming over total face value avoids enumerating every subset.
    states: dict[int, tuple[tuple[int, int, int], list[dict]]] = {0: ((0, 0, 0), [])}
    for asset in assets:
        for total, (key, selected) in list(states.items()):
            next_total = total + asset["value"]
            next_selected = selected + [asset]
            next_key = (
                key[0] + asset["value"],
                key[1] + asset["progress_lost"],
                key[2] + asset["property_count"],
            )
            existing = states.get(next_total)
            if existing is None or next_key < existing[0]:
                states[next_total] = (next_key, next_selected)

    covering = [
        (key, selected)
        for total, (key, selected) in states.items()
        if total >= amount_m
    ]
    return min(covering, key=lambda item: item[0])[1]


def _pay_debt_from_payment_assets(assets: list[dict]) -> PayDebt:
    money_indices: list[int] = []
    property_indices: list[tuple[int, int]] = []
    for asset in assets:
        if asset["kind"] == "m":
            money_indices.append(asset["index"])
        else:
            property_indices.append(asset["index"])
    return PayDebt(money_indices, property_indices)


def _choose_defend_steal(
    game: Game,
    moves: list[GameCommand],
    pending: SlyDealPending | ForcedDealPending | DealBreakerPending,
) -> GameCommand:
    # Victim (defender) wants to cancel; attacker (actor) wants the steal/swap to land.
    jsn = pending.jsn
    acting = game.acting_player_idx
    defender_idx = jsn.defender_idx
    actor_idx = jsn.actor_idx
    d_jsn = count_jsns(game.players[defender_idx])
    a_jsn = count_jsns(game.players[actor_idx])

    jsn_moves = [m for m in moves if isinstance(m, PlayJustSayNo)]
    pass_moves = [m for m in moves if isinstance(m, PassJustSayNo)]

    if isinstance(pending, DealBreakerPending) and jsn_moves:
        return jsn_moves[0]

    if acting == defender_idx:
        if jsn_moves and side_wins_if_plays_jsn(
            d_jsn, a_jsn, jsn.responder, jsn.chain_started, side="defender"
        ):
            return jsn_moves[0]
    elif acting == actor_idx and jsn_moves:
        if side_wins_if_plays_jsn(
            d_jsn, a_jsn, jsn.responder, jsn.chain_started, side="actor"
        ):
            return jsn_moves[0]

    if pass_moves:
        return pass_moves[0]
    return moves[0]


def _jsn_probability_for_amount(amount_m: int) -> float:
    """Linear scale: 0% at 1M, 100% at 14M+."""
    if amount_m >= 14:
        return 1.0
    if amount_m <= 1:
        return 0.0
    return (amount_m - 1) / 13


def _debtor_should_jsn(game: Game, pending: PaymentDue) -> bool:
    if count_jsns(game.players[pending.debtor_idx]) == 0:
        return False
    return game._rng.random() < _jsn_probability_for_amount(pending.amount_m)


def _best_pay_debt(game: Game, moves: list[PayDebt]) -> PayDebt:
    # Lexicographic ranking from rollout_strategy.md — earlier rules beat later ones.
    safe = [m for m in moves if not _pay_debt_breaks_complete_set(game, m)]
    pool = safe if safe else moves
    bank_only = [m for m in pool if not m.property_card_indices]
    pool = bank_only if bank_only else pool
    return min(
        pool,
        key=lambda m: (
            _pay_debt_total_value(game, m),
            _pay_debt_progress_lost(game, m),
            len(m.property_card_indices),
        ),
    )


def _pay_debt_breaks_complete_set(game: Game, move: PayDebt) -> bool:
    debtor = game.players[game.acting_player_idx]
    for set_idx, _ in move.property_card_indices:
        if debtor.pile_at(set_idx).is_complete():
            return True
    return False


def _pay_debt_total_value(game: Game, move: PayDebt) -> int:
    debtor = game.players[game.acting_player_idx]
    total = 0
    for i in move._selected_money_indices():
        total += debtor.money_pile[i].value
    for set_idx, card_idx in move._selected_property_indices():
        total += debtor.pile_at(set_idx).cards[card_idx].value
    return total


def _pay_debt_progress_lost(game: Game, move: PayDebt) -> int:
    debtor = game.players[game.acting_player_idx]
    lost = 0
    for set_idx, card_idx in move._selected_property_indices():
        pile = debtor.pile_at(set_idx)
        needed_before = _cards_needed(pile)
        # Paying from a one-away pile hurts more than face value alone.
        if needed_before == 1:
            lost += 100
        lost += _face_value_score(pile.cards[card_idx])
    return lost


def _deal_breaker_safe_vs(game: Game, victim_idx: int) -> bool:
    """Whether the victim can JSN-block a Deal Breaker (same for any of their complete sets)."""
    actor_idx = game.current_player_idx
    return not side_wins_if_plays_jsn(
        count_jsns(game.players[victim_idx]),
        count_jsns(game.players[actor_idx]),
        "defender",
        False,
        side="defender",
    )


def _deal_breaker_value(game: Game, move: PlayDealBreaker) -> int:
    victim = game.players[move.victim_idx]
    pile = victim.pile_at(move.victim_set_idx)
    value = sum(c.value for c in pile.cards)
    value += pile.building_bonus_m()
    return value


def _charge_amount(game: Game, move: GameCommand) -> int:
    # Rent owed is based on the charger's board for the chosen color.
    if isinstance(move, PlayRent):
        return rent_m_due_for_color(game.current_player(), move.charged_color)
    if isinstance(move, PlayDoubleRent):
        return rent_m_due_for_color(game.current_player(), move.charged_color) * 2
    if isinstance(move, PlayItsMyBirthday):
        return BIRTHDAY_GIFT_M
    if isinstance(move, PlayDebtCollector):
        return DEBT_COLLECTOR_PAYMENT_M
    return 0


def _pile_for_color(player: Player, color: Color) -> PropertySet | None:
    for pile in player.property_sets:
        if pile.color == color:
            return pile
    return None


def _cards_needed(pile: PropertySet) -> int:
    return CARDS_IN_SET_FOR_COLOR[pile.color] - len(pile.cards)


def _play_property_completes_set(game: Game, move: PlayPropertyFromHand) -> bool:
    pile = _pile_for_color(game.current_player(), move.into_color)
    if pile is None:
        return CARDS_IN_SET_FOR_COLOR[move.into_color] == 1
    return _cards_needed(pile) == 1


def _move_wild_completes_set(game: Game, move: MoveWildProperty) -> bool:
    pile = _pile_for_color(game.current_player(), move.into_color)
    if pile is None:
        return False
    return _cards_needed(pile) == 1


def _move_wild_breaks_complete_set(game: Game, move: MoveWildProperty) -> bool:
    """Moving a wild off a complete pile breaks that set (net-zero set progress)."""
    return game.current_player().pile_at(move.from_set_idx).is_complete()


def _sly_deal_completes_set(game: Game, move: PlaySlyDeal) -> bool:
    pile = _pile_for_color(game.current_player(), move.into_color)
    if pile is None:
        return CARDS_IN_SET_FOR_COLOR[move.into_color] == 1
    return _cards_needed(pile) == 1


def _stolen_card_value(game: Game, move: PlaySlyDeal) -> int:
    victim = game.players[move.target_player_idx]
    return victim.pile_at(move.target_set_idx).cards[move.target_card_idx].value


def _forced_deal_completes_set(game: Game, move: PlayForcedDeal) -> bool:
    actor = game.current_player()
    my_pile = actor.pile_at(move.my_set_idx)
    their_card = (
        game.players[move.target_player_idx]
        .pile_at(move.their_set_idx)
        .cards[move.their_card_idx]
    )
    return len(my_pile.cards) + 1 >= CARDS_IN_SET_FOR_COLOR[
        my_pile.color
    ] and their_card.can_count_as(my_pile.color)


def _forced_deal_breaks_own_set(game: Game, move: PlayForcedDeal) -> bool:
    actor = game.current_player()
    my_pile = actor.pile_at(move.my_set_idx)
    if _forced_deal_completes_set(game, move):
        return False
    # Giving away the last card before a complete set regresses our win progress.
    if _cards_needed(my_pile) == 1:
        return True
    return False


def _forced_deal_net_score(move: PlayForcedDeal, game: Game) -> int:
    actor = game.current_player()
    target = game.players[move.target_player_idx]
    my_pile = actor.pile_at(move.my_set_idx)
    their_pile = target.pile_at(move.their_set_idx)
    my_card = my_pile.cards[move.my_card_idx]
    their_card = their_pile.cards[move.their_card_idx]

    gain = _forced_deal_take_score(my_pile, their_card, target, their_pile)
    loss = _forced_deal_give_score(my_pile, my_card)
    return gain - loss


def _forced_deal_take_score(
    my_pile: PropertySet,
    their_card: PropertyCard,
    target: Player,
    their_pile: PropertySet,
) -> int:
    if len(my_pile.cards) + 1 >= CARDS_IN_SET_FOR_COLOR[my_pile.color]:
        return 1000
    needed = _cards_needed(my_pile)
    score = max(0, (CARDS_IN_SET_FOR_COLOR[my_pile.color] - needed) * 100)
    score += _face_value_score(their_card)
    # Pull from opponent piles near completion when they're close to winning.
    if _cards_needed(their_pile) == 1 and target.complete_set_count() >= 2:
        score += 50
    return score


def _forced_deal_give_score(
    my_pile: PropertySet,
    my_card: PropertyCard,
) -> int:
    # Singleton piles are ideal giveaways — the empty pile is removed after swap.
    if len(my_pile.cards) == 1:
        return 0
    needed = _cards_needed(my_pile)
    loss = _face_value_score(my_card)
    if needed == 1:
        loss += 100
    elif needed == 2:
        loss += 20
    # Wilds are flexible — costly to move off a pile that's using them.
    if isinstance(my_card, WildColorProperty) or isinstance(
        my_card, MultiColorProperty
    ):
        loss += 30
    return loss


def _discard_keep_score(card: Card, game: Game) -> int:
    """Higher score = prefer keeping this card when forced to discard."""
    board_colors = {p.color for p in game.current_player().property_sets}
    if isinstance(card, ActionCard):
        if card.action_type == ActionCardType.JUST_SAY_NO:
            return 10_000
        if card.action_type == ActionCardType.DEAL_BREAKER:
            return 10_000
        if card.action_type == ActionCardType.DOUBLE_RENT:
            return 10
        if card.action_type == ActionCardType.PASS_GO:
            return 200
        return 100 + _face_value_score(card)
    if isinstance(card, PropertyCard):
        return 500 + _face_value_score(card)
    if isinstance(card, (RentCard, WildRentCard)):
        if isinstance(card, RentCard) and (
            card.color1 in board_colors or card.color2 in board_colors
        ):
            return 800
        return 400
    return _face_value_score(card)


def _rent_colors_in_hand(player: Player) -> set[Color]:
    colors: set[Color] = set()
    for card in player.hand:
        if isinstance(card, RentCard):
            colors.add(card.color1)
            colors.add(card.color2)
        elif isinstance(card, WildRentCard):
            colors.update(Color)
    return colors


def _hand_card(game: Game, hand_index: int) -> Card:
    return game.current_player().hand[hand_index]


def _is_single_color_property(card: Card) -> bool:
    return isinstance(card, SingleColorProperty)


def _can_play_as_money(card: Card) -> bool:
    if isinstance(card, (RentCard, WildRentCard)):
        return False
    if isinstance(card, ActionCard):
        # Charge-only or too valuable to dump as face value; situational cards
        # (Forced Deal, Sly Deal, House, Hotel) stay eligible for priority 4.
        return card.action_type not in (
            ActionCardType.JUST_SAY_NO,
            ActionCardType.DEAL_BREAKER,
            ActionCardType.ITS_MY_BIRTHDAY,
            ActionCardType.DEBT_COLLECTOR,
            ActionCardType.DOUBLE_RENT,
        )
    return card.type != CardType.PROPERTY


def _first_of_type(moves: list[GameCommand], cmd_type: type) -> GameCommand | None:
    for move in moves:
        if isinstance(move, cmd_type):
            return move
    return None
