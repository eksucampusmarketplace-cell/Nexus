import api from './client'

export interface IntegrationType {
  id: string
  name: string
  description: string
  icon: string
  category: 'social' | 'development' | 'media' | 'utility' | 'web3'
  is_connected: boolean
  requires_auth: boolean
  features: string[]
}

export interface RSSFeedConfig {
  id: number
  name: string
  url: string
  check_interval: number
  max_items: number
  template?: string
  tags?: string[]
  is_active: boolean
  last_check?: string
  last_item?: string
  error_count: number
  created_at: string
}

export interface YouTubeConfig {
  id: number
  channel_id: string
  channel_name: string
  check_interval: number
  notify_live: boolean
  notify_shorts: boolean
  template?: string
  is_active: boolean
  last_video_id?: string
  created_at: string
}

export interface GitHubConfig {
  id: number
  repo_owner: string
  repo_name: string
  events: string[]
  branches: string[]
  notify_prs: boolean
  notify_issues: boolean
  notify_releases: boolean
  template?: string
  is_active: boolean
  created_at: string
}

export interface TwitterConfig {
  id: number
  username: string
  user_id?: string
  notify_tweets: boolean
  notify_replies: boolean
  notify_retweets: boolean
  include_media: boolean
  template?: string
  is_active: boolean
  last_tweet_id?: string
  created_at: string
}

export interface WebhookConfig {
  id: number
  name: string
  url: string
  secret?: string
  events: string[]
  method: 'POST' | 'GET' | 'PUT'
  headers?: Record<string, string>
  retry_count: number
  is_active: boolean
  last_triggered?: string
  created_at: string
}

export interface TwitchConfig {
  id: number
  channel_name: string
  channel_id?: string
  notify_live: boolean
  notify_offline: boolean
  include_clip: boolean
  template?: string
  is_active: boolean
  created_at: string
}

export interface SpotifyConfig {
  id: number
  playlist_id?: string
  artist_id?: string
  notify_new_releases: boolean
  notify_playlist_updates: boolean
  is_active: boolean
  created_at: string
}

export interface DiscordConfig {
  id: number
  webhook_url: string
  server_name?: string
  channel_name?: string
  forward_messages: boolean
  forward_format?: string
  is_active: boolean
  created_at: string
}

export interface IntegrationStats {
  total_integrations: number
  active_integrations: number
  total_webhooks_fired: number
  last_24h_events: number
  top_integration: string
  errors_24h: number
}

export interface IntegrationLog {
  id: number
  integration_type: string
  integration_id: number
  event_type: string
  status: 'success' | 'error' | 'pending'
  details?: Record<string, any>
  error_message?: string
  created_at: string
}

export const getAvailableIntegrations = async (groupId: number): Promise<IntegrationType[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/available`)
  return response.data
}

export const getIntegrationStats = async (groupId: number): Promise<IntegrationStats> => {
  const response = await api.get(`/groups/${groupId}/integrations/stats`)
  return response.data
}

export const getIntegrationLogs = async (
  groupId: number,
  integrationType?: string,
  limit = 50
): Promise<IntegrationLog[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/logs`, {
    params: { integration_type: integrationType, limit }
  })
  return response.data
}

// RSS Feed APIs
export const getRSSFeeds = async (groupId: number): Promise<RSSFeedConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/rss`)
  return response.data
}

export const addRSSFeed = async (groupId: number, data: Partial<RSSFeedConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/rss`, data)
  return response.data
}

export const updateRSSFeed = async (groupId: number, feedId: number, data: Partial<RSSFeedConfig>) => {
  const response = await api.patch(`/groups/${groupId}/integrations/rss/${feedId}`, data)
  return response.data
}

export const deleteRSSFeed = async (groupId: number, feedId: number) => {
  const response = await api.delete(`/groups/${groupId}/integrations/rss/${feedId}`)
  return response.data
}

export const testRSSFeed = async (groupId: number, url: string) => {
  const response = await api.post(`/groups/${groupId}/integrations/rss/test`, { url })
  return response.data
}

// YouTube APIs
export const getYouTubeChannels = async (groupId: number): Promise<YouTubeConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/youtube`)
  return response.data
}

export const addYouTubeChannel = async (groupId: number, data: Partial<YouTubeConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/youtube`, data)
  return response.data
}

export const updateYouTubeChannel = async (groupId: number, channelId: number, data: Partial<YouTubeConfig>) => {
  const response = await api.patch(`/groups/${groupId}/integrations/youtube/${channelId}`, data)
  return response.data
}

export const deleteYouTubeChannel = async (groupId: number, channelId: number) => {
  const response = await api.delete(`/groups/${groupId}/integrations/youtube/${channelId}`)
  return response.data
}

// GitHub APIs
export const getGitHubRepos = async (groupId: number): Promise<GitHubConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/github`)
  return response.data
}

export const addGitHubRepo = async (groupId: number, data: Partial<GitHubConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/github`, data)
  return response.data
}

export const updateGitHubRepo = async (groupId: number, repoId: number, data: Partial<GitHubConfig>) => {
  const response = await api.patch(`/groups/${groupId}/integrations/github/${repoId}`, data)
  return response.data
}

export const deleteGitHubRepo = async (groupId: number, repoId: number) => {
  const response = await api.delete(`/groups/${groupId}/integrations/github/${repoId}`)
  return response.data
}

// Twitter APIs
export const getTwitterAccounts = async (groupId: number): Promise<TwitterConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/twitter`)
  return response.data
}

export const addTwitterAccount = async (groupId: number, data: Partial<TwitterConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/twitter`, data)
  return response.data
}

export const updateTwitterAccount = async (groupId: number, accountId: number, data: Partial<TwitterConfig>) => {
  const response = await api.patch(`/groups/${groupId}/integrations/twitter/${accountId}`, data)
  return response.data
}

export const deleteTwitterAccount = async (groupId: number, accountId: number) => {
  const response = await api.delete(`/groups/${groupId}/integrations/twitter/${accountId}`)
  return response.data
}

// Webhook APIs
export const getWebhooks = async (groupId: number): Promise<WebhookConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/webhooks`)
  return response.data
}

export const addWebhook = async (groupId: number, data: Partial<WebhookConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/webhooks`, data)
  return response.data
}

export const updateWebhook = async (groupId: number, webhookId: number, data: Partial<WebhookConfig>) => {
  const response = await api.patch(`/groups/${groupId}/integrations/webhooks/${webhookId}`, data)
  return response.data
}

export const deleteWebhook = async (groupId: number, webhookId: number) => {
  const response = await api.delete(`/groups/${groupId}/integrations/webhooks/${webhookId}`)
  return response.data
}

export const testWebhook = async (groupId: number, webhookId: number) => {
  const response = await api.post(`/groups/${groupId}/integrations/webhooks/${webhookId}/test`)
  return response.data
}

export const regenerateWebhookSecret = async (groupId: number, webhookId: number) => {
  const response = await api.post(`/groups/${groupId}/integrations/webhooks/${webhookId}/regenerate-secret`)
  return response.data
}

// Additional integrations
export const getTwitchChannels = async (groupId: number): Promise<TwitchConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/twitch`)
  return response.data
}

export const addTwitchChannel = async (groupId: number, data: Partial<TwitchConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/twitch`, data)
  return response.data
}

export const getSpotifyConfigs = async (groupId: number): Promise<SpotifyConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/spotify`)
  return response.data
}

export const addSpotifyConfig = async (groupId: number, data: Partial<SpotifyConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/spotify`, data)
  return response.data
}

export const getDiscordConfigs = async (groupId: number): Promise<DiscordConfig[]> => {
  const response = await api.get(`/groups/${groupId}/integrations/discord`)
  return response.data
}

export const addDiscordConfig = async (groupId: number, data: Partial<DiscordConfig>) => {
  const response = await api.post(`/groups/${groupId}/integrations/discord`, data)
  return response.data
}
