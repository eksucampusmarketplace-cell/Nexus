import api from './client'

export interface ModerationAction {
  id: number
  action_type: string
  target_user_id: number
  actor_id: number
  reason: string | null
  duration_seconds: number | null
  silent: boolean
  ai_inferred: boolean
  created_at: string
}

export interface Warning {
  id: number
  reason: string
  created_at: string
  expires_at: string | null
  user: {
    id: number
    username: string | null
    first_name: string
  }
}

export interface ModerationStats {
  total_warnings: number
  total_mutes: number
  total_bans: number
  total_kicks: number
  active_mutes: number
  active_bans: number
}

export const getModerationStats = async (groupId: number): Promise<ModerationStats> => {
  const response = await api.get(`/groups/${groupId}/moderation/stats`)
  return response.data
}

export const getModerationQueue = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/moderation/queue`)
  return response.data
}

export const resolveModerationAction = async (
  groupId: number,
  actionId: number,
  action: 'approve' | 'dismiss' | 'custom',
  customAction?: { type: string; duration?: string; reason?: string }
) => {
  const response = await api.post(`/groups/${groupId}/moderation/queue/${actionId}/resolve`, {
    action,
    ...customAction,
  })
  return response.data
}

export const getWarnings = async (groupId: number, userId?: number) => {
  const params = userId ? { user_id: userId } : {}
  const response = await api.get(`/groups/${groupId}/warnings`, { params })
  return response.data
}

export const getMutes = async (groupId: number, active?: boolean) => {
  const params = active !== undefined ? { active } : {}
  const response = await api.get(`/groups/${groupId}/mutes`, { params })
  return response.data
}

export const getBans = async (groupId: number, active?: boolean) => {
  const params = active !== undefined ? { active } : {}
  const response = await api.get(`/groups/${groupId}/bans`, { params })
  return response.data
}

export const warnUser = async (groupId: number, userId: number, reason?: string, silent = false) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/warn`, {
    reason,
    silent,
  })
  return response.data
}

export const muteUser = async (
  groupId: number,
  userId: number,
  duration: string,
  reason?: string,
  silent = false
) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/mute`, {
    duration,
    reason,
    silent,
  })
  return response.data
}

export const banUser = async (
  groupId: number,
  userId: number,
  duration?: string,
  reason?: string,
  silent = false
) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/ban`, {
    duration,
    reason,
    silent,
  })
  return response.data
}

export const kickUser = async (groupId: number, userId: number, reason?: string) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/kick`, { reason })
  return response.data
}

export const unwarnUser = async (groupId: number, userId: number, warningId: number) => {
  const response = await api.delete(`/groups/${groupId}/warnings/${warningId}`)
  return response.data
}

export const unmuteUser = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/unmute`)
  return response.data
}

export const unbanUser = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/unban`)
  return response.data
}

export const approveUser = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/approve`)
  return response.data
}

export const unapproveUser = async (groupId: number, userId: number) => {
  const response = await api.delete(`/groups/${groupId}/members/${userId}/approve`)
  return response.data
}

export const trustUser = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/trust`)
  return response.data
}

export const untrustUser = async (groupId: number, userId: number) => {
  const response = await api.delete(`/groups/${groupId}/members/${userId}/trust`)
  return response.data
}

export const getMemberHistory = async (groupId: number, userId: number) => {
  const response = await api.get(`/groups/${groupId}/members/${userId}/history`)
  return response.data
}
