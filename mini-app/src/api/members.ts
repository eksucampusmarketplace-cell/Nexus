import api from './client'

export interface Member {
  id: number
  user_id: number
  group_id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  role: string
  trust_score: number
  xp: number
  level: number
  warn_count: number
  is_muted: boolean
  is_banned: boolean
  is_approved: boolean
  is_whitelisted: boolean
  joined_at: string
  message_count: number
}

export const listMembers = async (groupId: number, params?: {
  page?: number
  per_page?: number
  search?: string
  role?: string
}): Promise<Member[]> => {
  const response = await api.get(`/groups/${groupId}/members`, { params })
  return response.data
}

export const getMember = async (groupId: number, userId: number): Promise<Member> => {
  const response = await api.get(`/groups/${groupId}/members/${userId}`)
  return response.data
}

export const getMemberHistory = async (groupId: number, userId: number) => {
  const response = await api.get(`/groups/${groupId}/members/${userId}/history`)
  return response.data
}

export const warnMember = async (groupId: number, userId: number, data: {
  reason?: string
  silent?: boolean
}) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/warn`, data)
  return response.data
}

export const muteMember = async (groupId: number, userId: number, data: {
  duration?: string
  reason?: string
  silent?: boolean
}) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/mute`, data)
  return response.data
}

export const unmuteMember = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/unmute`)
  return response.data
}

export const banMember = async (groupId: number, userId: number, data: {
  duration?: string
  reason?: string
  silent?: boolean
}) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/ban`, data)
  return response.data
}

export const unbanMember = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/unban`)
  return response.data
}

export const kickMember = async (groupId: number, userId: number, reason?: string) => {
  const response = await api.post(`/groups/${groupId}/members/${userId}/kick`, { reason })
  return response.data
}
