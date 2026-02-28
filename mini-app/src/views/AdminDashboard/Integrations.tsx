import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  RSS,
  Youtube,
  Github,
  Webhook,
  Twitter,
  Plus,
  Trash2,
  RefreshCw,
  Loader2,
  CheckCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../stores/authStore'
import { useGroupStore } from '../../stores/groupStore'

interface RSSFeed {
  id: number
  name: string
  url: string
  tags: string
  is_active: boolean
  created_at: string
}

interface YouTubeChannel {
  id: number
  name: string
  handle: string
  url: string
  is_active: boolean
  created_at: string
}

interface GitHubRepo {
  id: number
  name: string
  url: string
  events: string
  is_active: boolean
  created_at: string
}

interface Webhook {
  id: number
  name: string
  url: string
  secret: string
  is_active: boolean
  created_at: string
}

interface TwitterAccount {
  id: number
  name: string
  handle: string
  is_active: boolean
  created_at: string
}

type TabType = 'rss' | 'youtube' | 'github' | 'webhooks' | 'twitter'

const tabs = [
  { id: 'rss', label: 'RSS Feeds', icon: RSS },
  { id: 'youtube', label: 'YouTube', icon: Youtube },
  { id: 'github', label: 'GitHub', icon: Github },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'twitter', label: 'Twitter/X', icon: Twitter },
]

export default function Integrations() {
  const { groupId } = useParams<{ groupId: string }>()
  const { token } = useAuthStore()
  const { currentGroup } = useGroupStore()
  
  const [activeTab, setActiveTab] = useState<TabType>('rss')
  const [rssFeeds, setRssFeeds] = useState<RSSFeed[]>([])
  const [youtubeChannels, setYoutubeChannels] = useState<YouTubeChannel[]>([])
  const [githubRepos, setGithubRepos] = useState<GitHubRepo[]>([])
  const [webhooks, setWebhooks] = useState<Webhook[]>([])
  const [twitterAccounts, setTwitterAccounts] = useState<TwitterAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [activeItem, setActiveItem] = useState<any>(null)

  useEffect(() => {
    if (!groupId) return
    
    loadIntegrations()
  }, [groupId])

  const loadIntegrations = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to load integrations')
      }
      
      const data = await response.json()
      setRssFeeds(data.rss_feeds || [])
      setYoutubeChannels(data.youtube_channels || [])
      setGithubRepos(data.github_repos || [])
      setWebhooks(data.webhooks || [])
      setTwitterAccounts(data.twitter_accounts || [])
    } catch (error) {
      toast.error('Failed to load integrations')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddRSS = async (data: any) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/rss`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        throw new Error('Failed to add RSS feed')
      }
      
      await loadIntegrations()
      toast.success('RSS feed added successfully')
      setShowAddModal(false)
    } catch (error) {
      toast.error('Failed to add RSS feed')
      console.error(error)
    }
  }

  const handleRemoveRSS = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/rss/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove RSS feed')
      }
      
      await loadIntegrations()
      toast.success('RSS feed removed')
    } catch (error) {
      toast.error('Failed to remove RSS feed')
      console.error(error)
    }
  }

  const handleToggleRSS = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/rss/${id}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to toggle RSS feed')
      }
      
      await loadIntegrations()
      toast.success('RSS feed updated')
    } catch (error) {
      toast.error('Failed to update RSS feed')
      console.error(error)
    }
  }

  const handleAddYouTube = async (data: any) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/youtube`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        throw new Error('Failed to add YouTube channel')
      }
      
      await loadIntegrations()
      toast.success('YouTube channel added')
      setShowAddModal(false)
    } catch (error) {
      toast.error('Failed to add YouTube channel')
      console.error(error)
    }
  }

  const handleRemoveYouTube = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/youtube/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove YouTube channel')
      }
      
      await loadIntegrations()
      toast.success('YouTube channel removed')
    } catch (error) {
      toast.error('Failed to remove YouTube channel')
      console.error(error)
    }
  }

  const handleAddGitHub = async (data: any) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/github`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        throw new Error('Failed to add GitHub repository')
      }
      
      await loadIntegrations()
      toast.success('GitHub repository added')
      setShowAddModal(false)
    } catch (error) {
      toast.error('Failed to add GitHub repository')
      console.error(error)
    }
  }

  const handleRemoveGitHub = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/github/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove GitHub repository')
      }
      
      await loadIntegrations()
      toast.success('GitHub repository removed')
    } catch (error) {
      toast.error('Failed to remove GitHub repository')
      console.error(error)
    }
  }

  const handleAddWebhook = async (data: any) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/webhooks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        throw new Error('Failed to add webhook')
      }
      
      await loadIntegrations()
      toast.success('Webhook added')
      setShowAddModal(false)
    } catch (error) {
      toast.error('Failed to add webhook')
      console.error(error)
    }
  }

  const handleRemoveWebhook = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/webhooks/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove webhook')
      }
      
      await loadIntegrations()
      toast.success('Webhook removed')
    } catch (error) {
      toast.error('Failed to remove webhook')
      console.error(error)
    }
  }

  const handleAddTwitter = async (data: any) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/twitter`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      
      if (!response.ok) {
        throw new Error('Failed to add Twitter account')
      }
      
      await loadIntegrations()
      toast.success('Twitter account added')
      setShowAddModal(false)
    } catch (error) {
      toast.error('Failed to add Twitter account')
      console.error(error)
    }
  }

  const handleRemoveTwitter = async (id: number) => {
    try {
      const response = await fetch(`/api/groups/${groupId}/integrations/twitter/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove Twitter account')
      }
      
      await loadIntegrations()
      toast.success('Twitter account removed')
    } catch (error) {
      toast.error('Failed to remove Twitter account')
      console.error(error)
    }
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'rss':
        return renderRSSFeeds()
      case 'youtube':
        return renderYouTubeChannels()
      case 'github':
        return renderGitHubRepos()
      case 'webhooks':
        return renderWebhooks()
      case 'twitter':
        return renderTwitterAccounts()
      default:
        return null
    }
  }

  const renderRSSFeeds = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">RSS Feeds</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {rssFeeds.length === 0 ? (
          <div className="text-center py-12">
            <RSS className="w-12 h-12 text-dark-500 mx-auto mb-4" />
            <p className="text-dark-400">No RSS feeds configured</p>
            <p className="text-sm text-dark-500 mt-2">
              Add RSS feeds to automatically post new articles to the group
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rssFeeds.map((feed) => (
              <div
                key={feed.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <RSS className="w-5 h-5 text-orange-500" />
                    <div>
                      <h4 className="font-semibold text-white">{feed.name}</h4>
                      <p className="text-sm text-dark-400 mt-1">
                        {feed.url}
                      </p>
                      {feed.tags && (
                        <div className="flex gap-1 mt-2">
                          {feed.tags.split(',').map((tag) => (
                            <span key={tag} className="px-2 py-1 bg-dark-800 rounded text-xs text-dark-300">
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleToggleRSS(feed.id)}
                      className={`w-10 h-6 rounded-lg transition-colors ${
                        feed.is_active
                          ? 'bg-green-600 hover:bg-green-700 text-white'
                          : 'bg-dark-800 hover:bg-dark-700 text-dark-300'
                      }`}
                    >
                      {feed.is_active ? <CheckCircle className="w-5 h-5" /> : <Loader2 className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => {
                        setActiveItem(feed)
                        setShowAddModal(true)
                      }}
                      className="p-2 text-dark-400 hover:text-dark-300 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleRemoveRSS(feed.id)}
                      className="p-2 text-red-400 hover:text-red-300 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-dark-500 mt-3">
                  Added {new Date(feed.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderYouTubeChannels = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">YouTube Channels</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {youtubeChannels.length === 0 ? (
          <div className="text-center py-12">
            <Youtube className="w-12 h-12 text-dark-500 mx-auto mb-4" />
            <p className="text-dark-400">No YouTube channels configured</p>
            <p className="text-sm text-dark-500 mt-2">
              Add YouTube channels to automatically post new videos to the group
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {youtubeChannels.map((channel) => (
              <div
                key={channel.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Youtube className="w-5 h-5 text-red-500" />
                    <div>
                      <h4 className="font-semibold text-white">{channel.name}</h4>
                      <p className="text-sm text-dark-400 mt-1">
                        @{channel.handle}
                      </p>
                      <a
                        href={channel.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 mt-1"
                      >
                        {channel.url}
                      </a>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRemoveYouTube(channel.id)}
                      className="p-2 text-red-400 hover:text-red-300 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-dark-500 mt-3">
                  Added {new Date(channel.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderGitHubRepos = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">GitHub Repositories</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {githubRepos.length === 0 ? (
          <div className="text-center py-12">
            <Github className="w-12 h-12 text-dark-500 mx-auto mb-4" />
            <p className="text-dark-400">No GitHub repositories configured</p>
            <p className="text-sm text-dark-500 mt-2">
              Add repositories to receive notifications for push, star, and release events
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {githubRepos.map((repo) => (
              <div
                key={repo.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Github className="w-5 h-5 text-white" />
                    <div>
                      <h4 className="font-semibold text-white">{repo.name}</h4>
                      <a
                        href={repo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 mt-1"
                      >
                        {repo.url}
                      </a>
                      <p className="text-xs text-green-400 mt-1">
                        Events: {repo.events}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveGitHub(repo.id)}
                    className="p-2 text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-dark-500 mt-3">
                  Added {new Date(repo.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderWebhooks = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Webhooks</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {webhooks.length === 0 ? (
          <div className="text-center py-12">
            <Webhook className="w-12 h-12 text-dark-500 mx-auto mb-4" />
            <p className="text-dark-400">No webhooks configured</p>
            <p className="text-sm text-dark-500 mt-2">
              Add webhooks to receive updates from external services
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {webhooks.map((webhook) => (
              <div
                key={webhook.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Webhook className="w-5 h-5 text-blue-400" />
                    <div>
                      <h4 className="font-semibold text-white">{webhook.name}</h4>
                      <p className="text-sm text-dark-400 mt-1">
                        {webhook.url}
                      </p>
                      <p className="text-xs text-yellow-400 mt-1">
                        Secret: ••••••••••••
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveWebhook(webhook.id)}
                    className="p-2 text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-dark-500 mt-3">
                  Added {new Date(webhook.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const renderTwitterAccounts = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Twitter/X Accounts</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {twitterAccounts.length === 0 ? (
          <div className="text-center py-12">
            <Twitter className="w-12 h-12 text-dark-500 mx-auto mb-4" />
            <p className="text-dark-400">No Twitter accounts configured</p>
            <p className="text-sm text-dark-500 mt-2">
              Add Twitter accounts to automatically post new tweets to the group
            </p>
            <p className="text-xs text-orange-400 mt-2">
              ⚠️ Twitter API access requires additional setup
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {twitterAccounts.map((account) => (
              <div
                key={account.id}
                className="bg-dark-900 rounded-xl border border-dark-800 p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Twitter className="w-5 h-5 text-sky-400" />
                    <div>
                      <h4 className="font-semibold text-white">{account.name}</h4>
                      <p className="text-sm text-dark-400 mt-1">
                        @{account.handle}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveTwitter(account.id)}
                    className="p-2 text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-dark-500 mt-3">
                  Added {new Date(account.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Integrations</h1>
        <p className="text-dark-400 mt-1">
          Manage external service integrations for your group
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-800 pb-4 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-purple-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {renderTabContent()}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-2xl border border-dark-700 p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">
                Add {tabs.find(t => t.id === activeTab)?.label.replace('s', '')?.slice(0, -1) || 'Integration'}
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-dark-400 hover:text-dark-300 transition-colors"
              >
                ✕
              </button>
            </div>
            <p className="text-sm text-dark-400 mb-6">
              {activeTab === 'rss' && 'Add RSS feed to automatically post new articles'}
              {activeTab === 'youtube' && 'Add YouTube channel to automatically post new videos'}
              {activeTab === 'github' && 'Add GitHub repository to receive notifications'}
              {activeTab === 'webhooks' && 'Add webhook to receive updates from external services'}
              {activeTab === 'twitter' && 'Add Twitter account to automatically post new tweets'}
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
