import axios from 'axios'

export interface RSSFeed {
  id: number
  name: string
  url: string
  tags: string
  is_active: boolean
  created_at: string
}

export interface YouTubeChannel {
  id: number
  name: string
  handle: string
  url: string
  is_active: boolean
  created_at: string
}

export interface GitHubRepo {
  id: number
  name: string
  url: string
  events: string
  is_active: boolean
  created_at: string
}

export interface Webhook {
  id: number
  name: string
  url: string
  secret: string
  is_active: boolean
  created_at: string
}

export interface TwitterAccount {
  id: number
  name: string
  handle: string
  is_active: boolean
  created_at: string
}

export interface IntegrationsResponse {
  rss_feeds: RSSFeed[]
  youtube_channels: YouTubeChannel[]
  github_repos: GitHubRepo[]
  webhooks: Webhook[]
  twitter_accounts: TwitterAccount[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export const integrationsAPI = {
  // RSS Feeds
  getRSSFeeds: async (groupId: number, token: string): Promise<RSSFeed[]> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations/rss`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data.rss_feeds || []
  },

  addRSSFeed: async (groupId: number, token: string, data: { name: string; url: string; tags: string }): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/rss`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    )
  },

  removeRSSFeed: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.delete(
      `${API_BASE}/api/groups/${groupId}/integrations/rss/${id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  toggleRSSFeed: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/rss/${id}/toggle`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  // YouTube Channels
  getYouTubeChannels: async (groupId: number, token: string): Promise<YouTubeChannel[]> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations/youtube`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data.youtube_channels || []
  },

  addYouTubeChannel: async (groupId: number, token: string, data: { name: string; handle: string; url: string }): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/youtube`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    )
  },

  removeYouTubeChannel: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.delete(
      `${API_BASE}/api/groups/${groupId}/integrations/youtube/${id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  // GitHub Repos
  getGitHubRepos: async (groupId: number, token: string): Promise<GitHubRepo[]> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations/github`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data.github_repos || []
  },

  addGitHubRepo: async (groupId: number, token: string, data: { name: string; url: string; events: string }): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/github`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    )
  },

  removeGitHubRepo: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.delete(
      `${API_BASE}/api/groups/${groupId}/integrations/github/${id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  // Webhooks
  getWebhooks: async (groupId: number, token: string): Promise<Webhook[]> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations/webhooks`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data.webhooks || []
  },

  addWebhook: async (groupId: number, token: string, data: { name: string; url: string; secret: string }): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/webhooks`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    )
  },

  removeWebhook: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.delete(
      `${API_BASE}/api/groups/${groupId}/integrations/webhooks/${id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  // Twitter Accounts
  getTwitterAccounts: async (groupId: number, token: string): Promise<TwitterAccount[]> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations/twitter`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data.twitter_accounts || []
  },

  addTwitterAccount: async (groupId: number, token: string, data: { name: string; handle: string }): Promise<void> => {
    await axios.post(
      `${API_BASE}/api/groups/${groupId}/integrations/twitter`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    )
  },

  removeTwitterAccount: async (groupId: number, token: string, id: number): Promise<void> => {
    await axios.delete(
      `${API_BASE}/api/groups/${groupId}/integrations/twitter/${id}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
  },

  // Get all integrations
  getAllIntegrations: async (groupId: number, token: string): Promise<IntegrationsResponse> => {
    const response = await axios.get<IntegrationsResponse>(
      `${API_BASE}/api/groups/${groupId}/integrations`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    return response.data
  },
}
