import api from './client'

export interface ExportJob {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_url: string | null
  created_at: string
  completed_at: string | null
}

export interface ImportJob {
  id: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  imported_count?: number
}

export const exportGroup = async (
  groupId: number,
  modules?: string[],
  format: 'json' | 'zip' = 'json'
): Promise<ExportJob> => {
  const response = await api.post(`/groups/${groupId}/export`, { modules, format })
  return response.data
}

export const getExportStatus = async (groupId: number, jobId: number): Promise<ExportJob> => {
  const response = await api.get(`/groups/${groupId}/export/${jobId}`)
  return response.data
}

export const downloadExport = async (groupId: number, jobId: number) => {
  const response = await api.get(`/groups/${groupId}/export/${jobId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

export const importGroup = async (
  groupId: number,
  file: File,
  modules?: string[],
  merge: boolean = false
): Promise<ImportJob> => {
  const formData = new FormData()
  formData.append('file', file)
  if (modules) formData.append('modules', JSON.stringify(modules))
  formData.append('merge', String(merge))

  const response = await api.post(`/groups/${groupId}/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getImportStatus = async (groupId: number, jobId: number): Promise<ImportJob> => {
  const response = await api.get(`/groups/${groupId}/import/${jobId}`)
  return response.data
}
