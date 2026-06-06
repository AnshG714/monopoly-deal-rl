import { useCallback, useState } from 'react'

import { applyMove, createGame } from '../api/client'
import type { CreateGameOptions, GameStateResponse } from '../api/types'

export function useGame() {
  const [game, setGame] = useState<GameStateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startGame = useCallback(async (options: CreateGameOptions = {}) => {
    setLoading(true)
    setError(null)
    try {
      const response = await createGame(options)
      setGame(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start game')
    } finally {
      setLoading(false)
    }
  }, [])

  const playMove = useCallback(
    async (moveId: number) => {
      if (!game) return
      setLoading(true)
      setError(null)
      try {
        const response = await applyMove(game.game_id, moveId)
        setGame(response)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Move failed')
      } finally {
        setLoading(false)
      }
    },
    [game],
  )

  return { game, loading, error, startGame, playMove }
}
