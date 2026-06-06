export interface Card {
  type: string;
  value: number;
  display_name?: string;
  action_type?: string;
  color?: string;
  color1?: string;
  color2?: string;
  property_kind?: string;
  name?: string;
  rents?: number[];
  color1_rents?: number[];
  color2_rents?: number[];
}

export interface HandCard extends Card {
  index: number;
}

export interface PropertySet {
  color: string;
  cards: Card[];
  complete: boolean;
  has_house: boolean;
  has_hotel: boolean;
}

export interface PlayerHand {
  size: number;
  cards: HandCard[] | null;
}

export interface Player {
  idx: number;
  name: string;
  complete_sets: number;
  hand: PlayerHand;
  bank: Card[];
  property_sets: PropertySet[];
}

export interface PendingState {
  kind: string;
  [key: string]: unknown;
}

export interface GameView {
  viewer_idx: number;
  current_player_idx: number;
  acting_player_idx: number;
  plays_this_turn: number;
  deck_size: number;
  discard_size: number;
  pending: PendingState | null;
  players: Player[];
}

export interface LegalMove {
  id: number;
  kind: string;
  label: string;
  params: Record<string, unknown>;
}

export interface GameStateResponse {
  game_id: string;
  viewer: number;
  acting_player_idx: number;
  current_player_idx: number;
  is_over: boolean;
  winner_idx: number | null;
  state: GameView;
  legal_moves: LegalMove[];
  seed?: number;
}

export interface DeckResponse {
  total: number;
  cards: Card[];
}

export interface CreateGameOptions {
  seed?: number;
  human_player_idx?: number;
  mcts_iterations?: number;
}
