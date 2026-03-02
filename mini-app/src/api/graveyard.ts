import api from './client'

export interface DeletedMessage {
  id: number
  message_id: number
  user_id: number
  content: string | null
  content_type: string
  deletion_reason: string
  deleted_by: number
  deleted_at: string
  can_restore: boolean
  restored_at: string | null
  restored_by: number | null
  restored_message_id: number | null
  trigger_word: string | null
  lock_type: string | null
  ai_confidence: number | null
  user_username: string | null
  user_first_name: string | null
  user_last_name: string | null
  deleter_username: string | null
  deleter_first_name: string | null
}

export interface GraveyardStats {
  total_deleted: number
  by_reason: Record<string, number>
  by_content_type: Record<string, number>
  recent_deletions_24h: number
  restored_count: number
  restoration_rate: number
}

export interface GraveyardListResponse {
  items: DeletedMessage[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface GraveyardFilters {
  deletion_reason?: string
  user_id?: number
  content_type?: string
  restored?: boolean
}

export async function getGraveyardMessages(
  groupId: number,
  page: number = 1,
  pageSize: number = 20,
  filters?: GraveyardFilters
): Promise<GraveyardListResponse> {
  const params = new URLSearchParams()
  params.append('page', page.toString())
  params.append('page_size', pageSize.toString())
  
  if (filters) {
    if (filters.deletion_reason) params.append('deletion_reason', filters.deletion_reason)
    if (filters.user_id) params.append('user_id', filters.user_id.toString())
    if (filters.content_type) params.append('content_type', filters.content_type)
    if (filters.restored !== undefined) params.append('restored', filters.restored.toString())
  }
  
  const response = await api.get(`/groups/${groupId}/graveyard?${params}`)
  return response.data
}

export async function getGraveyardStats(groupId: number): Promise<GraveyardStats> {
  const response = await api.get(`/groups/${groupId}/graveyard/stats`)
  return response.data
}

export async function getDeletedMessage(groupId: number, messageId: number): Promise<DeletedMessage> {
  const response = await api.get(`/groups/${groupId}/graveyard/${messageId}`)
  return response.data
}

export async function restoreMessage(groupId: number, messageId: number): Promise<{ success: boolean; new_message_id?: number }> {
  const response = await api.post(`/groups/${groupId}/graveyard/${messageId}/restore`)
  return response.data
}

export async function purgeMessage(groupId: number, messageId: number): Promise<{ success: boolean }> {
  const response = await api.delete(`/groups/${groupId}/graveyard/${messageId}`)
  return response.data
}
