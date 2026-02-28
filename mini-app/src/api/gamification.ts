import api from './client'

export interface Badge {
  id: number
  slug: string
  name: string
  description: string
  icon: string
  category: string
}

export interface MemberBadge {
  id: number
  badge_slug: string
  earned_at: string
  badge: Badge
}

export interface LevelConfig {
  enabled: boolean
  xp_per_message: number
  xp_per_reaction: number
  level_up_multiplier: number
  max_level: number
}

export interface MemberGamification {
  xp: number
  level: number
  next_level_xp: number
  progress_percent: number
  streak_days: number
  message_count: number
  badges: MemberBadge[]
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string | null
  first_name: string
  xp: number
  level: number
  badge_count: number
}

export interface Achievement {
  id: string
  name: string
  description: string
  icon: string
  category: string
  requirement: number
  progress: number
  unlocked: boolean
  unlocked_at?: string
}

export interface ReputationData {
  score: number
  given_today: number
  received_today: number
  rank: number
}

export interface ReputationLog {
  id: number
  from_user: {
    id: number
    username: string | null
    first_name: string
  }
  delta: number
  reason?: string
  created_at: string
}

export const getMemberGamification = async (groupId: number, userId?: number): Promise<MemberGamification> => {
  const url = userId 
    ? `/groups/${groupId}/gamification/members/${userId}`
    : `/groups/${groupId}/gamification/me`
  const response = await api.get(url)
  return response.data
}

export const getLeaderboard = async (groupId: number, type: 'xp' | 'level' | 'badges' = 'xp', limit = 20): Promise<LeaderboardEntry[]> => {
  const response = await api.get(`/groups/${groupId}/gamification/leaderboard`, {
    params: { type, limit }
  })
  return response.data
}

export const getAllBadges = async (groupId: number): Promise<Badge[]> => {
  const response = await api.get(`/groups/${groupId}/gamification/badges`)
  return response.data
}

export const getMemberBadges = async (groupId: number, userId?: number): Promise<MemberBadge[]> => {
  const url = userId
    ? `/groups/${groupId}/gamification/members/${userId}/badges`
    : `/groups/${groupId}/gamification/me/badges`
  const response = await api.get(url)
  return response.data
}

export const getAchievements = async (groupId: number): Promise<Achievement[]> => {
  const response = await api.get(`/groups/${groupId}/gamification/achievements`)
  return response.data
}

export const getReputation = async (groupId: number, userId?: number): Promise<ReputationData> => {
  const url = userId
    ? `/groups/${groupId}/gamification/members/${userId}/reputation`
    : `/groups/${groupId}/gamification/me/reputation`
  const response = await api.get(url)
  return response.data
}

export const getReputationHistory = async (groupId: number, userId?: number): Promise<ReputationLog[]> => {
  const url = userId
    ? `/groups/${groupId}/gamification/members/${userId}/reputation/history`
    : `/groups/${groupId}/gamification/me/reputation/history`
  const response = await api.get(url)
  return response.data
}

export const giveReputation = async (groupId: number, targetUserId: number, delta: number, reason?: string) => {
  const response = await api.post(`/groups/${groupId}/gamification/reputation`, {
    target_user_id: targetUserId,
    delta,
    reason
  })
  return response.data
}

export const getLevelConfig = async (groupId: number): Promise<LevelConfig> => {
  const response = await api.get(`/groups/${groupId}/gamification/config`)
  return response.data
}

export const updateLevelConfig = async (groupId: number, config: Partial<LevelConfig>) => {
  const response = await api.patch(`/groups/${groupId}/gamification/config`, config)
  return response.data
}

export const getGamificationStats = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/gamification/stats`)
  return response.data
}
