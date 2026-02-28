import api from './client'

export interface Lock {
  id: number
  lock_type: string
  is_locked: boolean
  mode: string
  mode_duration: number | null
  schedule_enabled: boolean
  schedule_windows: { from: string; to: string }[] | null
  allowlist: Record<string, string[]> | null
  updated_at: string
}

export const getLocks = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/locks`)
  return response.data
}

export const updateLock = async (
  groupId: number,
  lockType: string,
  data: {
    is_locked?: boolean
    mode?: string
    mode_duration?: number
    schedule_enabled?: boolean
    schedule_windows?: { from: string; to: string }[]
    allowlist?: Record<string, string[]>
  }
) => {
  const response = await api.patch(`/groups/${groupId}/locks/${lockType}`, data)
  return response.data
}

export const bulkUpdateLocks = async (
  groupId: number,
  locks: { lock_type: string; is_locked: boolean; mode?: string }[]
) => {
  const response = await api.post(`/groups/${groupId}/locks/bulk`, { locks })
  return response.data
}

export const getLockTypes = async () => {
  const response = await api.get('/locks/types')
  return response.data
}
