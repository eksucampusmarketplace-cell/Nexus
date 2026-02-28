import api from './client'

export interface Federation {
  id: string
  name: string
  description: string | null
  is_public: boolean
  owner_id: number
  created_at: string
  owner: {
    id: number
    username: string | null
    first_name: string
  }
  member_count?: number
  admin_count?: number
}

export interface FederationBan {
  id: number
  target_user: {
    id: number
    username: string | null
    first_name: string
    last_name: string | null
  }
  banned_by: {
    id: number
    username: string | null
    first_name: string
  }
  reason: string
  created_at: string
  expires_at: string | null
}

export const createFederation = async (data: { name: string; description?: string; is_public?: boolean }) => {
  const response = await api.post('/federations', data)
  return response.data
}

export const getMyFederations = async () => {
  const response = await api.get('/federations/my')
  return response.data
}

export const getFederation = async (fedId: string) => {
  const response = await api.get(`/federations/${fedId}`)
  return response.data
}

export const updateFederation = async (fedId: string, data: { name?: string; description?: string }) => {
  const response = await api.patch(`/federations/${fedId}`, data)
  return response.data
}

export const deleteFederation = async (fedId: string) => {
  const response = await api.delete(`/federations/${fedId}`)
  return response.data
}

export const joinFederation = async (fedId: string) => {
  const response = await api.post(`/federations/${fedId}/join`)
  return response.data
}

export const leaveFederation = async (fedId: string) => {
  const response = await api.post(`/federations/${fedId}/leave`)
  return response.data
}

export const getFederationBans = async (fedId: string) => {
  const response = await api.get(`/federations/${fedId}/bans`)
  return response.data
}

export const federateBan = async (
  fedId: string,
  data: { user_id: number; reason: string; duration?: string }
) => {
  const response = await api.post(`/federations/${fedId}/ban`, data)
  return response.data
}

export const federateUnban = async (fedId: string, userId: number) => {
  const response = await api.delete(`/federations/${fedId}/ban/${userId}`)
  return response.data
}

export const getFederationChats = async (fedId: string) => {
  const response = await api.get(`/federations/${fedId}/chats`)
  return response.data
}

export const addFederationAdmin = async (fedId: string, userId: number) => {
  const response = await api.post(`/federations/${fedId}/admins`, { user_id: userId })
  return response.data
}

export const removeFederationAdmin = async (fedId: string, userId: number) => {
  const response = await api.delete(`/federations/${fedId}/admins/${userId}`)
  return response.data
}

export const getFederationAdmins = async (fedId: string) => {
  const response = await api.get(`/federations/${fedId}/admins`)
  return response.data
}
