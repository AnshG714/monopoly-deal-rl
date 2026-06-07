import type {
  CreateGameOptions,
  DeckResponse,
  GameStateResponse,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function createGame(
  options: CreateGameOptions = {},
): Promise<GameStateResponse> {
  const res = await fetch(`${API_BASE}/api/games`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options),
  });
  return parseResponse<GameStateResponse>(res);
}

export async function getGame(gameId: string): Promise<GameStateResponse> {
  const res = await fetch(`${API_BASE}/api/games/${gameId}`);
  return parseResponse<GameStateResponse>(res);
}

export async function applyMove(
  gameId: string,
  moveId: number,
): Promise<GameStateResponse> {
  const res = await fetch(`${API_BASE}/api/games/${gameId}/moves`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move_id: moveId }),
  });
  return parseResponse<GameStateResponse>(res);
}

export async function getDeck(): Promise<DeckResponse> {
  const res = await fetch(`${API_BASE}/api/deck`);
  return parseResponse<DeckResponse>(res);
}
