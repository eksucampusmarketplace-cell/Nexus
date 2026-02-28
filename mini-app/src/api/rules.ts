import api from './client'

export interface Rule {
  id: number
  content: string
  created_at: string
  updated_at: string
  updated_by: {
    id: number
    username: string | null
    first_name: string
  } | null
}

export const getRules = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/rules`)
  return response.data
}

export const setRules = async (groupId: number, content: string) => {
  const response = await api.post(`/groups/${groupId}/rules`, { content })
  return response.data
}

export const resetRules = async (groupId: number) => {
  const response = await api.delete(`/groups/${groupId}/rules`)
  return response.data
}

export const getWelcomeSettings = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/greetings/welcome`)
  return response.data
}

export const updateWelcomeSettings = async (
  groupId: number,
  data: {
    content?: string
    media_file_id?: string
    media_type?: string
    has_buttons?: boolean
    button_data?: Record<string, unknown>
    delete_previous?: boolean
    delete_after_seconds?: number
    send_as_dm?: boolean
    is_enabled?: boolean
  }
) => {
  const response = await api.patch(`/groups/${groupId}/greetings/welcome`, data)
  return response.data
}

export const getGoodbyeSettings = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/greetings/goodbye`)
  return response.data
}

export const updateGoodbyeSettings = async (
  groupId: number,
  data: {
    content?: string
    media_file_id?: string
    media_type?: string
    has_buttons?: boolean
    button_data?: Record<string, unknown>
    delete_previous?: boolean
    is_enabled?: boolean
  }
) => {
  const response = await api.patch(`/groups/${groupId}/greetings/goodbye`, data)
  return response.data
}
