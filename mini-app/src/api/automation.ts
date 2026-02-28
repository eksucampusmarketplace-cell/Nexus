import api from './client'

export interface Workflow {
  id: number
  name: string
  description?: string
  trigger_type: 'keyword' | 'command' | 'schedule' | 'event' | 'new_member' | 'message'
  trigger_config: Record<string, any>
  actions: WorkflowAction[]
  is_enabled: boolean
  run_count: number
  last_run_at?: string
  created_at: string
}

export interface WorkflowAction {
  id: string
  type: 'send_message' | 'delete_message' | 'warn_user' | 'mute_user' | 'kick_user' | 'assign_role' | 'send_dm' | 'wait' | 'condition' | 'http_request'
  config: Record<string, any>
  delay_seconds?: number
}

export interface KeywordResponder {
  id: number
  keywords: string[]
  match_type: 'contains' | 'exact' | 'starts_with' | 'regex'
  case_sensitive: boolean
  responses: string[]
  random_response: boolean
  media_type?: string
  media_file_id?: string
  delete_trigger: boolean
  cooldown_seconds: number
  trigger_count: number
  is_active: boolean
  last_triggered_at?: string
}

export interface CustomCommand {
  id: number
  command: string
  description?: string
  response_type: 'text' | 'media' | 'sticker' | 'animation'
  response_content: string
  response_media?: string
  buttons?: Record<string, any>
  allow_variables: boolean
  require_args: boolean
  admin_only: boolean
  usage_count: number
  is_active: boolean
  created_at: string
}

export interface AutomationStats {
  total_workflows: number
  active_workflows: number
  total_triggers: number
  keyword_responders: number
  custom_commands: number
  top_triggers: { name: string; count: number }[]
}

export interface TriggerLog {
  id: number
  workflow_id?: number
  responder_id?: number
  trigger_type: string
  triggered_by: number
  trigger_data: Record<string, any>
  actions_executed: number
  success: boolean
  error?: string
  created_at: string
}

export const getWorkflows = async (groupId: number): Promise<Workflow[]> => {
  const response = await api.get(`/groups/${groupId}/automation/workflows`)
  return response.data
}

export const createWorkflow = async (groupId: number, data: Partial<Workflow>) => {
  const response = await api.post(`/groups/${groupId}/automation/workflows`, data)
  return response.data
}

export const updateWorkflow = async (groupId: number, workflowId: number, data: Partial<Workflow>) => {
  const response = await api.patch(`/groups/${groupId}/automation/workflows/${workflowId}`, data)
  return response.data
}

export const deleteWorkflow = async (groupId: number, workflowId: number) => {
  const response = await api.delete(`/groups/${groupId}/automation/workflows/${workflowId}`)
  return response.data
}

export const toggleWorkflow = async (groupId: number, workflowId: number, isEnabled: boolean) => {
  const response = await api.post(`/groups/${groupId}/automation/workflows/${workflowId}/toggle`, {
    is_enabled: isEnabled
  })
  return response.data
}

export const getKeywordResponders = async (groupId: number): Promise<KeywordResponder[]> => {
  const response = await api.get(`/groups/${groupId}/automation/responders`)
  return response.data
}

export const createKeywordResponder = async (groupId: number, data: Partial<KeywordResponder>) => {
  const response = await api.post(`/groups/${groupId}/automation/responders`, data)
  return response.data
}

export const updateKeywordResponder = async (groupId: number, responderId: number, data: Partial<KeywordResponder>) => {
  const response = await api.patch(`/groups/${groupId}/automation/responders/${responderId}`, data)
  return response.data
}

export const deleteKeywordResponder = async (groupId: number, responderId: number) => {
  const response = await api.delete(`/groups/${groupId}/automation/responders/${responderId}`)
  return response.data
}

export const getCustomCommands = async (groupId: number): Promise<CustomCommand[]> => {
  const response = await api.get(`/groups/${groupId}/automation/commands`)
  return response.data
}

export const createCustomCommand = async (groupId: number, data: Partial<CustomCommand>) => {
  const response = await api.post(`/groups/${groupId}/automation/commands`, data)
  return response.data
}

export const updateCustomCommand = async (groupId: number, commandId: number, data: Partial<CustomCommand>) => {
  const response = await api.patch(`/groups/${groupId}/automation/commands/${commandId}`, data)
  return response.data
}

export const deleteCustomCommand = async (groupId: number, commandId: number) => {
  const response = await api.delete(`/groups/${groupId}/automation/commands/${commandId}`)
  return response.data
}

export const getAutomationStats = async (groupId: number): Promise<AutomationStats> => {
  const response = await api.get(`/groups/${groupId}/automation/stats`)
  return response.data
}

export const getTriggerLogs = async (groupId: number, limit = 50): Promise<TriggerLog[]> => {
  const response = await api.get(`/groups/${groupId}/automation/logs`, {
    params: { limit }
  })
  return response.data
}

export const testWorkflow = async (groupId: number, workflowId: number, testData: Record<string, any>) => {
  const response = await api.post(`/groups/${groupId}/automation/workflows/${workflowId}/test`, testData)
  return response.data
}

export const testKeywordResponder = async (groupId: number, responderId: number, testMessage: string) => {
  const response = await api.post(`/groups/${groupId}/automation/responders/${responderId}/test`, {
    message: testMessage
  })
  return response.data
}
