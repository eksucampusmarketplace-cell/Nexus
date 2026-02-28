import api from './client'

export interface BroadcastMessage {
  id: number
  content: string
  media_file_id?: string
  media_type?: string
  button_data?: Record<string, any>
  target_type: 'all' | 'role' | 'active' | 'inactive' | 'custom'
  target_filter?: Record<string, any>
  scheduled_at?: string
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed'
  sent_count: number
  failed_count: number
  created_at: string
  sent_at?: string
}

export interface ChannelConfig {
  id: number
  channel_id: number
  channel_name: string
  channel_username?: string
  channel_type: 'announcement' | 'updates' | 'moderation' | 'general'
  is_active: boolean
  auto_post_enabled: boolean
  format_template?: string
  include_source: boolean
  include_media: boolean
  total_posts: number
  added_at: string
}

export interface BroadcastStats {
  total_broadcasts: number
  total_sent: number
  total_failed: number
  average_open_rate: number
  recent_broadcasts: BroadcastMessage[]
}

export interface MessageTemplate {
  id: number
  name: string
  content: string
  media_file_id?: string
  media_type?: string
  button_data?: Record<string, any>
  variables: string[]
  category: string
  usage_count: number
  created_at: string
}

export const getBroadcasts = async (groupId: number, status?: string): Promise<BroadcastMessage[]> => {
  const response = await api.get(`/groups/${groupId}/broadcasts`, {
    params: { status }
  })
  return response.data
}

export const createBroadcast = async (groupId: number, data: Partial<BroadcastMessage>) => {
  const response = await api.post(`/groups/${groupId}/broadcasts`, data)
  return response.data
}

export const scheduleBroadcast = async (groupId: number, broadcastId: number, scheduledAt: string) => {
  const response = await api.post(`/groups/${groupId}/broadcasts/${broadcastId}/schedule`, {
    scheduled_at: scheduledAt
  })
  return response.data
}

export const cancelBroadcast = async (groupId: number, broadcastId: number) => {
  const response = await api.post(`/groups/${groupId}/broadcasts/${broadcastId}/cancel`)
  return response.data
}

export const deleteBroadcast = async (groupId: number, broadcastId: number) => {
  const response = await api.delete(`/groups/${groupId}/broadcasts/${broadcastId}`)
  return response.data
}

export const getBroadcastStats = async (groupId: number): Promise<BroadcastStats> => {
  const response = await api.get(`/groups/${groupId}/broadcasts/stats`)
  return response.data
}

export const getChannelConfigs = async (groupId: number): Promise<ChannelConfig[]> => {
  const response = await api.get(`/groups/${groupId}/channels`)
  return response.data
}

export const addChannel = async (groupId: number, data: Partial<ChannelConfig>) => {
  const response = await api.post(`/groups/${groupId}/channels`, data)
  return response.data
}

export const updateChannel = async (groupId: number, channelId: number, data: Partial<ChannelConfig>) => {
  const response = await api.patch(`/groups/${groupId}/channels/${channelId}`, data)
  return response.data
}

export const removeChannel = async (groupId: number, channelId: number) => {
  const response = await api.delete(`/groups/${groupId}/channels/${channelId}`)
  return response.data
}

export const postToChannel = async (groupId: number, channelId: number, content: string, options?: Record<string, any>) => {
  const response = await api.post(`/groups/${groupId}/channels/${channelId}/post`, {
    content,
    ...options
  })
  return response.data
}

export const getMessageTemplates = async (groupId: number): Promise<MessageTemplate[]> => {
  const response = await api.get(`/groups/${groupId}/broadcasts/templates`)
  return response.data
}

export const createMessageTemplate = async (groupId: number, data: Partial<MessageTemplate>) => {
  const response = await api.post(`/groups/${groupId}/broadcasts/templates`, data)
  return response.data
}

export const updateMessageTemplate = async (groupId: number, templateId: number, data: Partial<MessageTemplate>) => {
  const response = await api.patch(`/groups/${groupId}/broadcasts/templates/${templateId}`, data)
  return response.data
}

export const deleteMessageTemplate = async (groupId: number, templateId: number) => {
  const response = await api.delete(`/groups/${groupId}/broadcasts/templates/${templateId}`)
  return response.data
}

export const previewBroadcast = async (groupId: number, data: Partial<BroadcastMessage>) => {
  const response = await api.post(`/groups/${groupId}/broadcasts/preview`, data)
  return response.data
}

export const getBroadcastRecipients = async (groupId: number, broadcastId: number) => {
  const response = await api.get(`/groups/${groupId}/broadcasts/${broadcastId}/recipients`)
  return response.data
}
