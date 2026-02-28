import api from './client'

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  language_code: string
  is_premium: boolean
}

export const telegramAuth = async (initData: string): Promise<AuthResponse & { user: User }> => {
  const response = await api.post('/auth/token', { init_data: initData })
  return response.data
}

export const getMe = async (): Promise<User> => {
  const response = await api.get('/auth/me')
  return response.data
}

export const getPermissions = async (groupId: number) => {
  const response = await api.get(`/auth/permissions/${groupId}`)
  return response.data
}
