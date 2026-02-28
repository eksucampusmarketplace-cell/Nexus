import api from './client'

export interface Module {
  name: string
  version: string
  author: string
  description: string
  category: string
  dependencies: string[]
  conflicts: string[]
  is_enabled: boolean
  commands: Array<{
    name: string
    description: string
    admin_only: boolean
    aliases: string[]
  }>
}

export const listModules = async (): Promise<Module[]> => {
  const response = await api.get('/modules/registry')
  return response.data
}

export const listGroupModules = async (groupId: number): Promise<Module[]> => {
  const response = await api.get(`/groups/${groupId}/modules`)
  return response.data
}

export const enableModule = async (groupId: number, moduleName: string) => {
  const response = await api.post(`/groups/${groupId}/modules/${moduleName}/enable`)
  return response.data
}

export const disableModule = async (groupId: number, moduleName: string) => {
  const response = await api.post(`/groups/${groupId}/modules/${moduleName}/disable`)
  return response.data
}

export const getModuleConfig = async (groupId: number, moduleName: string) => {
  const response = await api.get(`/groups/${groupId}/modules/${moduleName}/config`)
  return response.data
}

export const updateModuleConfig = async (groupId: number, moduleName: string, config: Record<string, unknown>) => {
  const response = await api.patch(`/groups/${groupId}/modules/${moduleName}/config`, { config })
  return response.data
}
