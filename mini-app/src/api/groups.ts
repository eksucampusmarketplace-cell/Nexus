import api from './client'

export interface Group {
  id: number
  telegram_id: number
  title: string
  username: string | null
  member_count: number
  language: string
  is_premium: boolean
  owner_id: number
  created_at: string
}

export interface GroupStats {
  total_members: number
  active_members_24h: number
  active_members_7d: number
  new_members_24h: number
  messages_24h: number
  top_members: Array<{
    id: number
    username: string
    first_name: string
    message_count: number
    xp: number
    level: number
  }>
  mood_score: number
}

export const listGroups = async (): Promise<Group[]> => {
  const response = await api.get('/groups')
  return response.data
}

export const getGroup = async (groupId: number): Promise<Group> => {
  const response = await api.get(`/groups/${groupId}`)
  return response.data
}

export const updateGroup = async (groupId: number, data: Partial<Group>): Promise<Group> => {
  const response = await api.patch(`/groups/${groupId}`, data)
  return response.data
}

export const getGroupStats = async (groupId: number): Promise<GroupStats> => {
  const response = await api.get(`/groups/${groupId}/stats`)
  return response.data
}
