import api from './client'

export interface SystemStats {
  total_users: number
  total_groups: number
  active_groups: number
  total_members: number
  custom_bots: number
  recent_users_24h: number
  owner_count: number
  support_count: number
}

export interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  language_code: string | null
  is_premium: boolean
  created_at: string
  last_seen: string
  is_owner: boolean
  is_support: boolean
}

export interface Group {
  id: number
  telegram_id: number
  title: string
  username: string | null
  member_count: number
  language: string
  is_premium: boolean
  timezone: string
  created_at: string
  updated_at: string
  has_custom_bot: boolean
}

export interface SystemConfig {
  environment: string
  owner_count: number
  support_count: number
  features: {
    ai_enabled: boolean
    custom_bots_enabled: boolean
    webhooks_enabled: boolean
  }
}

export const getSystemStats = async (): Promise<SystemStats> => {
  const response = await api.get('/admin/stats')
  return response.data
}

export const listUsers = async (limit = 100, offset = 0): Promise<User[]> => {
  const response = await api.get('/admin/users', { params: { limit, offset } })
  return response.data
}

export const listAllGroups = async (limit = 100, offset = 0): Promise<Group[]> => {
  const response = await api.get('/admin/groups', { params: { limit, offset } })
  return response.data
}

export const getSystemConfig = async (): Promise<SystemConfig> => {
  const response = await api.get('/admin/config')
  return response.data
}

export const toggleSupportStatus = async (userId: number, isSupport: boolean): Promise<{
  success: boolean
  user_id: number
  telegram_id: number
  is_support: boolean
  note: string
}> => {
  const response = await api.post(`/admin/users/${userId}/toggle-support`, null, {
    params: { is_support: isSupport }
  })
  return response.data
}
