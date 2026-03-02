import api from './client'

export { default as api } from './client'

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

export const telegramAuth = async (initData: string, customBotToken?: string): Promise<AuthResponse & { user: User }> => {
  try {
    const payload: { init_data: string; bot_token?: string } = { init_data: initData }
    if (customBotToken) {
      payload.bot_token = customBotToken
    }
    const response = await api.post('/auth/token', payload)
    
    // Store token in localStorage
    if (response.data.access_token) {
      localStorage.setItem('nexus_token', response.data.access_token)
    }
    
    return response.data
  } catch (error: any) {
    console.error('Telegram auth failed:', error.response?.data || error.message)
    throw error
  }
}

export const getMe = async (): Promise<User> => {
  const response = await api.get('/auth/me')
  return response.data
}

export const getPermissions = async (groupId: number) => {
  const response = await api.get(`/auth/permissions/${groupId}`)
  return response.data
}
