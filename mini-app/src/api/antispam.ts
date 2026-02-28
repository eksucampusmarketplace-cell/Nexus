import api from './client'

export interface AntifloodConfig {
  is_enabled: boolean
  message_limit: number
  window_seconds: number
  action: string
  action_duration: number
  media_flood_enabled: boolean
  media_limit: number
}

export interface AntiraidConfig {
  is_enabled: boolean
  join_threshold: number
  window_seconds: number
  action: string
  auto_unlock_after: number
  notify_admins: boolean
}

export interface BannedWord {
  id: number
  word: string
  list_number: number
  is_regex: boolean
  is_enabled: boolean
  created_at: string
  created_by: {
    id: number
    username: string | null
    first_name: string
  }
}

export interface BannedWordListConfig {
  list_number: number
  action: string
  action_duration: number | null
  delete_message: boolean
}

export const getAntifloodConfig = async (groupId: number): Promise<AntifloodConfig> => {
  const response = await api.get(`/groups/${groupId}/antiflood`)
  return response.data
}

export const updateAntifloodConfig = async (
  groupId: number,
  config: Partial<AntifloodConfig>
): Promise<AntifloodConfig> => {
  const response = await api.patch(`/groups/${groupId}/antiflood`, config)
  return response.data
}

export const getAntiraidConfig = async (groupId: number): Promise<AntiraidConfig> => {
  const response = await api.get(`/groups/${groupId}/antiraid`)
  return response.data
}

export const updateAntiraidConfig = async (
  groupId: number,
  config: Partial<AntiraidConfig>
): Promise<AntiraidConfig> => {
  const response = await api.patch(`/groups/${groupId}/antiraid`, config)
  return response.data
}

export const getBannedWords = async (groupId: number, listNumber?: number) => {
  const params = listNumber ? { list_number: listNumber } : {}
  const response = await api.get(`/groups/${groupId}/blocklist`, { params })
  return response.data
}

export const addBannedWord = async (
  groupId: number,
  data: { word: string; list_number: number; is_regex?: boolean }
) => {
  const response = await api.post(`/groups/${groupId}/blocklist`, data)
  return response.data
}

export const removeBannedWord = async (groupId: number, wordId: number) => {
  const response = await api.delete(`/groups/${groupId}/blocklist/${wordId}`)
  return response.data
}

export const getBannedWordListConfig = async (groupId: number, listNumber: number) => {
  const response = await api.get(`/groups/${groupId}/blocklist/${listNumber}/config`)
  return response.data
}

export const updateBannedWordListConfig = async (
  groupId: number,
  listNumber: number,
  config: { action: string; action_duration?: number; delete_message?: boolean }
) => {
  const response = await api.patch(`/groups/${groupId}/blocklist/${listNumber}/config`, config)
  return response.data
}
