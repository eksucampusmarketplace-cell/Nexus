import api from './client'

export interface Note {
  id: number
  keyword: string
  content: string
  is_private: boolean
  has_buttons: boolean
  button_data: Record<string, unknown> | null
  media_file_id: string | null
  media_type: string | null
  created_at: string
  created_by: {
    id: number
    username: string | null
    first_name: string
  }
}

export interface Filter {
  id: number
  trigger: string
  match_type: string
  response_type: string
  response_content: string
  action: string | null
  delete_trigger: boolean
  admin_only: boolean
  case_sensitive: boolean
  created_at: string
  created_by: {
    id: number
    username: string | null
    first_name: string
  }
}

export const getNotes = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/notes`)
  return response.data
}

export const createNote = async (
  groupId: number,
  data: {
    keyword: string
    content: string
    is_private?: boolean
    media_file_id?: string
    media_type?: string
    has_buttons?: boolean
    button_data?: Record<string, unknown>
  }
) => {
  const response = await api.post(`/groups/${groupId}/notes`, data)
  return response.data
}

export const updateNote = async (groupId: number, noteId: number, data: Partial<Note>) => {
  const response = await api.patch(`/groups/${groupId}/notes/${noteId}`, data)
  return response.data
}

export const deleteNote = async (groupId: number, noteId: number) => {
  const response = await api.delete(`/groups/${groupId}/notes/${noteId}`)
  return response.data
}

export const getFilters = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/filters`)
  return response.data
}

export const createFilter = async (
  groupId: number,
  data: {
    trigger: string
    match_type: string
    response_type: string
    response_content: string
    action?: string
    delete_trigger?: boolean
    admin_only?: boolean
    case_sensitive?: boolean
  }
) => {
  const response = await api.post(`/groups/${groupId}/filters`, data)
  return response.data
}

export const updateFilter = async (groupId: number, filterId: number, data: Partial<Filter>) => {
  const response = await api.patch(`/groups/${groupId}/filters/${filterId}`, data)
  return response.data
}

export const deleteFilter = async (groupId: number, filterId: number) => {
  const response = await api.delete(`/groups/${groupId}/filters/${filterId}`)
  return response.data
}

export const testFilter = async (groupId: number, trigger: string) => {
  const response = await api.post(`/groups/${groupId}/filters/test`, { trigger })
  return response.data
}
