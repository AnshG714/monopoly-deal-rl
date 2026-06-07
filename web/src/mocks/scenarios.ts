import type { GameStateResponse, LegalMove, Player } from "@/api/types";

import {
  dealBreaker,
  forcedDeal,
  handCard,
  justSayNo,
  money,
  property,
  slyDeal,
  wildProperty,
} from "./cards";

export interface MockScenario {
  id: string;
  label: string;
  description: string;
}

const VIEWER = 0;
const OPPONENT = 1;

function baseState(
  id: string,
  options: {
    pending: GameStateResponse["state"]["pending"];
    legal_moves: LegalMove[];
    acting_player_idx?: number;
    current_player_idx?: number;
    viewer?: Player;
    opponent?: Player;
  },
): GameStateResponse {
  const viewer =
    options.viewer ??
    ({
      idx: VIEWER,
      name: "You",
      complete_sets: 0,
      hand: { size: 0, cards: [] },
      bank: [],
      property_sets: [],
    } satisfies Player);

  const opponent =
    options.opponent ??
    ({
      idx: OPPONENT,
      name: "Opponent",
      complete_sets: 0,
      hand: { size: 5, cards: null },
      bank: [money(1), money(2)],
      property_sets: [],
    } satisfies Player);

  const actingPlayerIdx = options.acting_player_idx ?? VIEWER;
  const currentPlayerIdx = options.current_player_idx ?? actingPlayerIdx;

  return {
    game_id: `mock-${id}`,
    viewer: VIEWER,
    acting_player_idx: actingPlayerIdx,
    current_player_idx: currentPlayerIdx,
    is_over: false,
    winner_idx: null,
    seed: 0,
    state: {
      viewer_idx: VIEWER,
      current_player_idx: currentPlayerIdx,
      acting_player_idx: actingPlayerIdx,
      plays_this_turn: 2,
      deck_size: 80,
      discard_size: 4,
      discard_top: {
        type: "action",
        value: 3,
        display_name: "Sly Deal",
        action_type: "sly_deal",
      },
      pending: options.pending,
      players: [viewer, opponent],
    },
    legal_moves: options.legal_moves,
  };
}

function debtPaymentScenario(): GameStateResponse {
  const viewer: Player = {
    idx: VIEWER,
    name: "You",
    complete_sets: 0,
    hand: {
      size: 2,
      cards: [handCard(money(1), 0), handCard(property("St. James Place", "orange", 2, [1, 2, 3, 4]), 1)],
    },
    bank: [money(1), money(2), money(4)],
    property_sets: [
      {
        color: "red",
        cards: [
          property("Kentucky Avenue", "red", 2, [1, 2, 3, 5]),
          property("Indiana Avenue", "red", 3, [1, 2, 4, 6]),
        ],
        complete: false,
        has_house: false,
        has_hotel: false,
      },
    ],
  };

  return baseState("debt-payment", {
    acting_player_idx: VIEWER,
    pending: {
      kind: "PaymentDue",
      creditor_idx: OPPONENT,
      debtor_idx: VIEWER,
      amount_m: 5,
    },
    viewer,
    legal_moves: [
      {
        id: 0,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: { money_pile_indices: [2], property_card_indices: [] },
      },
      {
        id: 1,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: { money_pile_indices: [1, 2], property_card_indices: [] },
      },
      {
        id: 2,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: { money_pile_indices: [0, 1, 2], property_card_indices: [] },
      },
      {
        id: 3,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: { money_pile_indices: [0, 2], property_card_indices: [] },
      },
      {
        id: 4,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: { money_pile_indices: [], property_card_indices: [[0, 1]] },
      },
      {
        id: 5,
        kind: "PayDebt",
        label: "PayDebt (You responds)",
        params: {
          money_pile_indices: [1],
          property_card_indices: [[0, 0]],
        },
      },
    ],
  });
}

function debtWithJsnScenario(): GameStateResponse {
  const scenario = debtPaymentScenario();
  return {
    ...scenario,
    game_id: "mock-debt-with-jsn",
    state: {
      ...scenario.state,
      players: [
        {
          ...scenario.state.players[0],
          hand: {
            size: 1,
            cards: [handCard(justSayNo(), 0)],
          },
        },
        scenario.state.players[1],
      ],
    },
    legal_moves: [
      ...scenario.legal_moves,
      {
        id: 6,
        kind: "PlayJustSayNo",
        label: "PlayJustSayNo (You responds)",
        params: { hand_index: 0 },
      },
    ],
  };
}

function paymentJsnCounterScenario(): GameStateResponse {
  return baseState("payment-jsn-counter", {
    acting_player_idx: VIEWER,
    viewer: {
      idx: VIEWER,
      name: "You",
      complete_sets: 1,
      hand: {
        size: 1,
        cards: [handCard(justSayNo(), 0)],
      },
      bank: [money(4), money(3)],
      property_sets: [],
    },
    opponent: {
      idx: OPPONENT,
      name: "Opponent",
      complete_sets: 0,
      hand: { size: 4, cards: null },
      bank: [money(2)],
      property_sets: [
        {
          color: "green",
          cards: [
            property("Pacific Avenue", "green", 2, [1, 2, 4, 7]),
            property("North Carolina Avenue", "green", 3, [1, 2, 4, 7]),
            property("Pennsylvania Avenue", "green", 4, [2, 3, 6, 8]),
          ],
          complete: true,
          has_house: false,
          has_hotel: false,
        },
      ],
    },
    pending: {
      kind: "PaymentDue",
      creditor_idx: VIEWER,
      debtor_idx: OPPONENT,
      amount_m: 6,
      jsn: {
        defender_idx: OPPONENT,
        actor_idx: VIEWER,
        responder: "actor",
        chain_started: true,
      },
    },
    legal_moves: [
      {
        id: 0,
        kind: "PassJustSayNo",
        label: "PassJustSayNo (You responds)",
        params: {},
      },
      {
        id: 1,
        kind: "PlayJustSayNo",
        label: "PlayJustSayNo (You responds)",
        params: { hand_index: 0 },
      },
    ],
  });
}

function slyDealDefenseScenario(): GameStateResponse {
  const stolenCard = property("Connecticut Avenue", "light_blue", 2, [1, 2, 3, 4]);
  return baseState("sly-deal-defense", {
    acting_player_idx: VIEWER,
    viewer: {
      idx: VIEWER,
      name: "You",
      complete_sets: 0,
      hand: {
        size: 1,
        cards: [handCard(justSayNo(), 0)],
      },
      bank: [money(3)],
      property_sets: [
        {
          color: "light_blue",
          cards: [
            property("Oriental Avenue", "light_blue", 1, [1, 2, 3, 4]),
            stolenCard,
          ],
          complete: false,
          has_house: false,
          has_hotel: false,
        },
      ],
    },
    pending: {
      kind: "SlyDealPending",
      actor_idx: OPPONENT,
      victim_idx: VIEWER,
      target_set_idx: 0,
      target_card_idx: 1,
      into_color: "light_blue",
    },
    legal_moves: [
      {
        id: 0,
        kind: "PassJustSayNo",
        label: "PassJustSayNo (You responds)",
        params: {},
      },
      {
        id: 1,
        kind: "PlayJustSayNo",
        label: "PlayJustSayNo (You responds)",
        params: { hand_index: 0 },
      },
    ],
  });
}

function forcedDealDefenseScenario(): GameStateResponse {
  return baseState("forced-deal-defense", {
    acting_player_idx: VIEWER,
    viewer: {
      idx: VIEWER,
      name: "You",
      complete_sets: 0,
      hand: { size: 0, cards: [] },
      bank: [money(2)],
      property_sets: [
        {
          color: "yellow",
          cards: [property("Atlantic Avenue", "yellow", 3, [1, 2, 4, 6])],
          complete: false,
          has_house: false,
          has_hotel: false,
        },
      ],
    },
    opponent: {
      idx: OPPONENT,
      name: "Opponent",
      complete_sets: 0,
      hand: { size: 3, cards: null },
      bank: [],
      property_sets: [
        {
          color: "pink",
          cards: [property("Virginia Avenue", "pink", 2, [1, 2, 3, 4])],
          complete: false,
          has_house: false,
          has_hotel: false,
        },
      ],
    },
    pending: {
      kind: "ForcedDealPending",
      actor_idx: OPPONENT,
      target_player_idx: VIEWER,
      my_set_idx: 0,
      my_card_idx: 0,
      their_set_idx: 0,
      their_card_idx: 0,
      take_into_color: "light_blue",
      give_into_color: "pink",
    },
    legal_moves: [
      {
        id: 0,
        kind: "PassJustSayNo",
        label: "PassJustSayNo (You responds)",
        params: {},
      },
    ],
  });
}

function dealBreakerDefenseScenario(): GameStateResponse {
  return baseState("deal-breaker-defense", {
    acting_player_idx: VIEWER,
    viewer: {
      idx: VIEWER,
      name: "You",
      complete_sets: 1,
      hand: {
        size: 1,
        cards: [handCard(justSayNo(), 0)],
      },
      bank: [money(1), money(4)],
      property_sets: [
        {
          color: "brown",
          cards: [
            property("Mediterranean Avenue", "brown", 1, [1, 2, 3, 4]),
            property("Baltic Avenue", "brown", 1, [1, 2, 3, 4]),
          ],
          complete: true,
          has_house: false,
          has_hotel: false,
        },
        {
          color: "railroad",
          cards: [property("Reading Railroad", "railroad", 2, [1, 2, 3, 4])],
          complete: false,
          has_house: false,
          has_hotel: false,
        },
      ],
    },
    pending: {
      kind: "DealBreakerPending",
      actor_idx: OPPONENT,
      victim_idx: VIEWER,
      victim_set_idx: 0,
    },
    legal_moves: [
      {
        id: 0,
        kind: "PassJustSayNo",
        label: "PassJustSayNo (You responds)",
        params: {},
      },
      {
        id: 1,
        kind: "PlayJustSayNo",
        label: "PlayJustSayNo (You responds)",
        params: { hand_index: 0 },
      },
    ],
  });
}

function dealActionsPlayScenario(): GameStateResponse {
  const viewer: Player = {
    idx: VIEWER,
    name: "You",
    complete_sets: 0,
    hand: {
      size: 3,
      cards: [
        handCard(slyDeal(), 0),
        handCard(forcedDeal(), 1),
        handCard(dealBreaker(), 2),
      ],
    },
    bank: [money(2)],
    property_sets: [
      {
        color: "yellow",
        cards: [property("Atlantic Avenue", "yellow", 3, [1, 2, 4, 6])],
        complete: false,
        has_house: false,
        has_hotel: false,
      },
      {
        color: "red",
        cards: [property("Kentucky Avenue", "red", 2, [1, 2, 3, 5])],
        complete: false,
        has_house: false,
        has_hotel: false,
      },
    ],
  };

  const opponent: Player = {
    idx: OPPONENT,
    name: "Opponent",
    complete_sets: 1,
    hand: { size: 4, cards: null },
    bank: [money(1), money(3)],
    property_sets: [
      {
        color: "light_blue",
        cards: [
          property("Oriental Avenue", "light_blue", 1, [1, 2, 3, 4]),
          property("Connecticut Avenue", "light_blue", 2, [1, 2, 3, 4]),
          wildProperty(),
        ],
        complete: false,
        has_house: false,
        has_hotel: false,
      },
      {
        color: "pink",
        cards: [property("Virginia Avenue", "pink", 2, [1, 2, 3, 4])],
        complete: false,
        has_house: false,
        has_hotel: false,
      },
      {
        color: "brown",
        cards: [
          property("Mediterranean Avenue", "brown", 1, [1, 2, 3, 4]),
          property("Baltic Avenue", "brown", 1, [1, 2, 3, 4]),
        ],
        complete: true,
        has_house: false,
        has_hotel: false,
      },
    ],
  };

  return baseState("deal-actions-play", {
    acting_player_idx: VIEWER,
    current_player_idx: VIEWER,
    pending: null,
    viewer,
    opponent,
    legal_moves: [
      // Sly Deal (hand 0) — any card in opponent's incomplete light_blue pile
      {
        id: 0,
        kind: "PlaySlyDeal",
        label: "PlaySlyDeal",
        params: {
          hand_index: 0,
          target_player_idx: OPPONENT,
          target_set_idx: 0,
          target_card_idx: 0,
          into_color: "light_blue",
        },
      },
      {
        id: 1,
        kind: "PlaySlyDeal",
        label: "PlaySlyDeal",
        params: {
          hand_index: 0,
          target_player_idx: OPPONENT,
          target_set_idx: 0,
          target_card_idx: 1,
          into_color: "light_blue",
        },
      },
      // Wild can land on several of your piles — triggers the color-pick step
      {
        id: 2,
        kind: "PlaySlyDeal",
        label: "PlaySlyDeal",
        params: {
          hand_index: 0,
          target_player_idx: OPPONENT,
          target_set_idx: 0,
          target_card_idx: 2,
          into_color: "red",
        },
      },
      {
        id: 3,
        kind: "PlaySlyDeal",
        label: "PlaySlyDeal",
        params: {
          hand_index: 0,
          target_player_idx: OPPONENT,
          target_set_idx: 0,
          target_card_idx: 2,
          into_color: "yellow",
        },
      },
      {
        id: 4,
        kind: "PlaySlyDeal",
        label: "PlaySlyDeal",
        params: {
          hand_index: 0,
          target_player_idx: OPPONENT,
          target_set_idx: 0,
          target_card_idx: 2,
          into_color: "light_blue",
        },
      },
      // Forced Deal (hand 1) — Atlantic ↔ Virginia
      {
        id: 5,
        kind: "PlayForcedDeal",
        label: "PlayForcedDeal",
        params: {
          hand_index: 1,
          target_player_idx: OPPONENT,
          my_set_idx: 0,
          my_card_idx: 0,
          their_set_idx: 1,
          their_card_idx: 0,
        },
      },
      // Forced Deal — Kentucky ↔ Virginia
      {
        id: 6,
        kind: "PlayForcedDeal",
        label: "PlayForcedDeal",
        params: {
          hand_index: 1,
          target_player_idx: OPPONENT,
          my_set_idx: 1,
          my_card_idx: 0,
          their_set_idx: 1,
          their_card_idx: 0,
        },
      },
      // Deal Breaker (hand 2) — steal complete brown set
      {
        id: 7,
        kind: "PlayDealBreaker",
        label: "PlayDealBreaker",
        params: {
          hand_index: 2,
          victim_idx: OPPONENT,
          victim_set_idx: 2,
        },
      },
      {
        id: 8,
        kind: "EndTurn",
        label: "EndTurn",
        params: {},
      },
    ],
  });
}

function idleAfterInterruptScenario(): GameStateResponse {
  return baseState("idle", {
    acting_player_idx: VIEWER,
    pending: null,
    viewer: {
      idx: VIEWER,
      name: "You",
      complete_sets: 0,
      hand: {
        size: 3,
        cards: [
          handCard(money(1), 0),
          handCard(money(2), 1),
          handCard(property("Vermont Avenue", "light_blue", 1, [1, 2, 3, 4]), 2),
        ],
      },
      bank: [money(3)],
      property_sets: [],
    },
    legal_moves: [
      {
        id: 0,
        kind: "EndTurn",
        label: "EndTurn",
        params: {},
      },
    ],
  });
}

const SCENARIO_BUILDERS: Record<string, () => GameStateResponse> = {
  "debt-payment": debtPaymentScenario,
  "debt-with-jsn": debtWithJsnScenario,
  "payment-jsn-counter": paymentJsnCounterScenario,
  "sly-deal-defense": slyDealDefenseScenario,
  "forced-deal-defense": forcedDealDefenseScenario,
  "deal-breaker-defense": dealBreakerDefenseScenario,
  "deal-actions-play": dealActionsPlayScenario,
  idle: idleAfterInterruptScenario,
};

export const MOCK_SCENARIOS: MockScenario[] = [
  {
    id: "debt-payment",
    label: "Debt payment",
    description: "You owe $5M — pick bank cards and properties",
  },
  {
    id: "debt-with-jsn",
    label: "Debt + JSN option",
    description: "You owe $5M and can pay or play Just Say No",
  },
  {
    id: "payment-jsn-counter",
    label: "Payment JSN chain",
    description: "Opponent said No to your rent — counter or accept",
  },
  {
    id: "sly-deal-defense",
    label: "Sly Deal defense",
    description: "Opponent is stealing Connecticut Avenue",
  },
  {
    id: "forced-deal-defense",
    label: "Forced Deal defense",
    description: "Opponent wants to swap Atlantic for Virginia",
  },
  {
    id: "deal-breaker-defense",
    label: "Deal Breaker defense",
    description: "Opponent is stealing your complete brown set",
  },
  {
    id: "deal-actions-play",
    label: "Deal actions (your turn)",
    description:
      "Sly Deal, Forced Deal & Deal Breaker in hand — drag to discard pile",
  },
];

export function getMockScenario(id: string): GameStateResponse {
  const builder = SCENARIO_BUILDERS[id];
  if (!builder) {
    throw new Error(`Unknown mock scenario: ${id}`);
  }
  return builder();
}

export function isMockGame(game: GameStateResponse | null): boolean {
  return game?.game_id.startsWith("mock-") ?? false;
}

export function resolveMockMove(
  game: GameStateResponse,
  moveId: number,
): GameStateResponse {
  const move = game.legal_moves.find((candidate) => candidate.id === moveId);
  if (!move) {
    throw new Error(`Mock move ${moveId} not found`);
  }

  if (
    move.kind === "PlayJustSayNo" &&
    game.state.pending?.kind === "PaymentDue" &&
    !game.state.pending.jsn
  ) {
    return getMockScenario("payment-jsn-counter");
  }

  if (move.kind === "PlaySlyDeal") {
    return getMockScenario("sly-deal-defense");
  }

  if (move.kind === "PlayForcedDeal") {
    return getMockScenario("forced-deal-defense");
  }

  if (move.kind === "PlayDealBreaker") {
    return getMockScenario("deal-breaker-defense");
  }

  return getMockScenario("idle");
}
