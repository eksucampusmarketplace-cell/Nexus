import api from './client'

export interface SearchResult {
  type: 'message' | 'user' | 'moderation' | 'note' | 'filter'
  id: number
  title: string
  content?: string
  metadata: Record<string, any>
  relevance: number
  created_at: string
}

export interface SearchFilters {
  types?: string[]
  date_from?: string
  date_to?: string
  user_id?: number
  moderator_id?: number
  action_type?: string
  role?: string
}

export interface SearchStats {
  total_messages: number
  total_users: number
  total_moderations: number
  total_notes: number
  recent_searches: string[]
}

export interface AdvancedSearchQuery {
  query: string
  filters: SearchFilters
  sort_by: 'relevance' | 'date' | 'popularity'
  sort_order: 'asc' | 'desc'
  page: number
  page_size: number
}

export interface UserSearchResult {
  id: number
  user_id: number
  username: string | null
  first_name: string
  role: string
  joined_at: string
  message_count: number
  xp: number
  level: number
  is_muted: boolean
  is_banned: boolean
  warn_count: number
}

export interface ModerationSearchResult {
  id: number
  action_type: string
  target_user: {
    id: number
    username: string | null
    first_name: string
  }
  actor: {
    id: number
    username: string | null
    first_name: string
  }
  reason?: string
  duration?: string
  created_at: string
  reversed: boolean
}

export interface MessageSearchResult {
  id: number
  message_id: number
  user: {
    id: number
    username: string | null
    first_name: string
  }
  content: string
  message_type: string
  created_at: string
  has_media: boolean
}

export const search = async (groupId: number, query: AdvancedSearchQuery): Promise<{
  results: SearchResult[]
  total: number
  page: number
  page_size: number
}> => {
  const response = await api.post(`/groups/${groupId}/search`, query)
  return response.data
}

export const searchUsers = async (
  groupId: number,
  query: string,
  filters?: Partial<SearchFilters>
): Promise<UserSearchResult[]> => {
  const response = await api.get(`/groups/${groupId}/search/users`, {
    params: { q: query, ...filters }
  })
  return response.data
}

export const searchModerations = async (
  groupId: number,
  query: string,
  filters?: Partial<SearchFilters>
): Promise<ModerationSearchResult[]> => {
  const response = await api.get(`/groups/${groupId}/search/moderations`, {
    params: { q: query, ...filters }
  })
  return response.data
}

export const searchMessages = async (
  groupId: number,
  query: string,
  filters?: Partial<SearchFilters>
): Promise<MessageSearchResult[]> => {
  const response = await api.get(`/groups/${groupId}/search/messages`, {
    params: { q: query, ...filters }
  })
  return response.data
}

export const getSearchStats = async (groupId: number): Promise<SearchStats> => {
  const response = await api.get(`/groups/${groupId}/search/stats`)
  return response.data
}

export const getRecentSearches = async (groupId: number, limit = 10): Promise<string[]> => {
  const response = await api.get(`/groups/${groupId}/search/recent`, {
    params: { limit }
  })
  return response.data
}

export const getFilterOptions = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/search/filters`)
  return response.data
}

export const exportSearchResults = async (groupId: number, searchId: string, format: 'json' | 'csv') => {
  const response = await api.post(`/groups/${groupId}/search/export`, {
    search_id: searchId,
    format
  })
  return response.data
}
