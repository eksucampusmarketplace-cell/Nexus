import api from './client'

export interface GameConfig {
  enabled_games: string[]
  cooldown_seconds: number
  min_bet: number
  max_bet: number
  house_edge_percent: number
  rewards_enabled: boolean
  daily_game_limit: number
}

export interface GameSession {
  id: number
  game_type: string
  status: 'active' | 'ended' | 'cancelled'
  data: Record<string, any>
  created_at: string
  ended_at?: string
}

export interface GameScore {
  id: number
  user_id: number
  username: string | null
  first_name: string
  game_type: string
  score: number
  created_at: string
}

export interface GameLeaderboard {
  game_type: string
  entries: GameScore[]
  total_plays: number
  unique_players: number
}

export interface GameStats {
  total_sessions: number
  total_plays: number
  unique_players: number
  most_played: string
  total_wagered: number
  total_paid_out: number
}

export interface GameReward {
  id: number
  name: string
  description: string
  game_type: string
  requirement_type: 'wins' | 'plays' | 'streak' | 'score'
  requirement_value: number
  reward_coins: number
  reward_xp: number
  reward_badge?: string
  icon: string
  unlocked: boolean
  progress: number
  unlocked_at?: string
}

export interface ActiveGame {
  id: number
  game_type: string
  players: {
    user_id: number
    username: string | null
    first_name: string
    is_ready: boolean
  }[]
  current_turn?: number
  status: 'waiting' | 'playing' | 'ended'
  created_at: string
}

export const getGameConfig = async (groupId: number): Promise<GameConfig> => {
  const response = await api.get(`/groups/${groupId}/games/config`)
  return response.data
}

export const updateGameConfig = async (groupId: number, config: Partial<GameConfig>) => {
  const response = await api.patch(`/groups/${groupId}/games/config`, config)
  return response.data
}

export const getAvailableGames = async (groupId: number): Promise<string[]> => {
  const response = await api.get(`/groups/${groupId}/games/available`)
  return response.data
}

export const getGameLeaderboard = async (groupId: number, gameType?: string): Promise<GameLeaderboard[]> => {
  const response = await api.get(`/groups/${groupId}/games/leaderboard`, {
    params: { game_type: gameType }
  })
  return response.data
}

export const getGameStats = async (groupId: number): Promise<GameStats> => {
  const response = await api.get(`/groups/${groupId}/games/stats`)
  return response.data
}

export const getGameRewards = async (groupId: number, userId?: number): Promise<GameReward[]> => {
  const url = userId
    ? `/groups/${groupId}/games/rewards?user_id=${userId}`
    : `/groups/${groupId}/games/rewards`
  const response = await api.get(url)
  return response.data
}

export const getActiveGames = async (groupId: number): Promise<ActiveGame[]> => {
  const response = await api.get(`/groups/${groupId}/games/active`)
  return response.data
}

export const createGameSession = async (groupId: number, gameType: string, data?: Record<string, any>) => {
  const response = await api.post(`/groups/${groupId}/games/sessions`, {
    game_type: gameType,
    data
  })
  return response.data
}

export const joinGameSession = async (groupId: number, sessionId: number) => {
  const response = await api.post(`/groups/${groupId}/games/sessions/${sessionId}/join`)
  return response.data
}

export const makeGameMove = async (groupId: number, sessionId: number, move: Record<string, any>) => {
  const response = await api.post(`/groups/${groupId}/games/sessions/${sessionId}/move`, move)
  return response.data
}

export const getGameHistory = async (groupId: number, userId?: number, limit = 20) => {
  const response = await api.get(`/groups/${groupId}/games/history`, {
    params: { user_id: userId, limit }
  })
  return response.data
}

export const claimGameReward = async (groupId: number, rewardId: number) => {
  const response = await api.post(`/groups/${groupId}/games/rewards/${rewardId}/claim`)
  return response.data
}
