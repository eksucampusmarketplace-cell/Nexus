import api from './client'

export interface BotToken {
  bot_telegram_id: number
  bot_username: string
  bot_name: string
  is_active: boolean
  registered_at: string
}

export const registerBotToken = async (groupId: number, token: string): Promise<BotToken> => {
  const response = await api.post(`/groups/${groupId}/token`, { token })
  return response.data
}

export const getBotToken = async (groupId: number): Promise<BotToken | null> => {
  const response = await api.get(`/groups/${groupId}/token`)
  return response.data
}

export const revokeBotToken = async (groupId: number) => {
  const response = await api.delete(`/groups/${groupId}/token`)
  return response.data
}

export const validateBotToken = async (token: string): Promise<{
  valid: boolean
  bot?: {
    id: number
    username: string
    name: string
  }
  error?: string
}> => {
  const response = await api.post('/bots/validate-token', { token })
  return response.data
}
