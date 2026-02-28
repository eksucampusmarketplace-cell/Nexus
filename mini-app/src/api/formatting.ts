import api from './client'

export interface TextTemplate {
  id: number
  name: string
  content: string
  category: 'welcome' | 'rules' | 'announcement' | 'moderation' | 'fun' | 'custom'
  variables: string[]
  preview_text?: string
  usage_count: number
  is_public: boolean
  created_at: string
}

export interface ButtonConfig {
  id: number
  name: string
  buttons: ButtonRow[]
  layout: 'inline' | 'vertical'
  created_at: string
}

export interface ButtonRow {
  id: string
  buttons: {
    id: string
    text: string
    type: 'url' | 'callback' | 'switch_inline'
    value: string
    style?: 'primary' | 'secondary' | 'danger'
  }[]
}

export interface FormattingPreset {
  id: number
  name: string
  description?: string
  formatting: {
    bold?: boolean
    italic?: boolean
    underline?: boolean
    strikethrough?: boolean
    spoiler?: boolean
    code?: boolean
    pre?: boolean
    link?: string
    mention?: string
  }
  emoji_style: 'native' | 'custom' | 'none'
}

export interface RichTextEditor {
  id: number
  name: string
  content: string
  formatting: Record<string, any>
  media?: {
    type: 'photo' | 'video' | 'animation' | 'document'
    file_id: string
    caption?: string
  }
  buttons?: ButtonConfig
  created_at: string
  updated_at: string
}

export const getTextTemplates = async (groupId: number, category?: string): Promise<TextTemplate[]> => {
  const response = await api.get(`/groups/${groupId}/formatting/templates`, {
    params: { category }
  })
  return response.data
}

export const createTextTemplate = async (groupId: number, data: Partial<TextTemplate>) => {
  const response = await api.post(`/groups/${groupId}/formatting/templates`, data)
  return response.data
}

export const updateTextTemplate = async (groupId: number, templateId: number, data: Partial<TextTemplate>) => {
  const response = await api.patch(`/groups/${groupId}/formatting/templates/${templateId}`, data)
  return response.data
}

export const deleteTextTemplate = async (groupId: number, templateId: number) => {
  const response = await api.delete(`/groups/${groupId}/formatting/templates/${templateId}`)
  return response.data
}

export const getButtonConfigs = async (groupId: number): Promise<ButtonConfig[]> => {
  const response = await api.get(`/groups/${groupId}/formatting/buttons`)
  return response.data
}

export const createButtonConfig = async (groupId: number, data: Partial<ButtonConfig>) => {
  const response = await api.post(`/groups/${groupId}/formatting/buttons`, data)
  return response.data
}

export const updateButtonConfig = async (groupId: number, configId: number, data: Partial<ButtonConfig>) => {
  const response = await api.patch(`/groups/${groupId}/formatting/buttons/${configId}`, data)
  return response.data
}

export const deleteButtonConfig = async (groupId: number, configId: number) => {
  const response = await api.delete(`/groups/${groupId}/formatting/buttons/${configId}`)
  return response.data
}

export const previewFormatting = async (groupId: number, content: string, formatting?: Record<string, any>) => {
  const response = await api.post(`/groups/${groupId}/formatting/preview`, {
    content,
    formatting
  })
  return response.data
}

export const getFormattingPresets = async (groupId: number): Promise<FormattingPreset[]> => {
  const response = await api.get(`/groups/${groupId}/formatting/presets`)
  return response.data
}

export const createFormattingPreset = async (groupId: number, data: Partial<FormattingPreset>) => {
  const response = await api.post(`/groups/${groupId}/formatting/presets`, data)
  return response.data
}

export const generateButtonCode = async (groupId: number, buttons: ButtonRow[]) => {
  const response = await api.post(`/groups/${groupId}/formatting/generate-buttons`, { buttons })
  return response.data
}

export const validateFormatting = async (groupId: number, content: string) => {
  const response = await api.post(`/groups/${groupId}/formatting/validate`, { content })
  return response.data
}

export const applyEmojiFormatting = async (groupId: number, content: string, style: string) => {
  const response = await api.post(`/groups/${groupId}/formatting/emoji`, {
    content,
    style
  })
  return response.data
}

export const getVariableReference = async (groupId: number) => {
  const response = await api.get(`/groups/${groupId}/formatting/variables`)
  return response.data
}
