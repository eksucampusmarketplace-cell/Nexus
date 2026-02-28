import api from './client'

export interface CaptchaSettings {
  captcha_type: 'none' | 'button' | 'math' | 'quiz' | 'image'
  timeout_seconds: number
  action_on_fail: 'kick' | 'ban' | 'restrict'
  mute_on_join: boolean
  custom_text: string | null
}

export const getCaptchaSettings = async (groupId: number): Promise<CaptchaSettings> => {
  const response = await api.get(`/groups/${groupId}/captcha`)
  return response.data
}

export const updateCaptchaSettings = async (
  groupId: number,
  settings: Partial<CaptchaSettings>
): Promise<CaptchaSettings> => {
  const response = await api.patch(`/groups/${groupId}/captcha`, settings)
  return response.data
}

export const resetCaptcha = async (groupId: number, userId: number) => {
  const response = await api.post(`/groups/${groupId}/captcha/reset`, { user_id: userId })
  return response.data
}

export const getCaptchaStats = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/captcha/stats`)
  return response.data
}
