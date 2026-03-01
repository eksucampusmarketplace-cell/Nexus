import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plug, Rss, Youtube, Github, Webhook, Twitter, PlusCircle } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'

const mockFeeds = [
  { id: 1, type: 'rss', name: 'Tech News', url: 'https://example.com/feed', status: 'active' },
  { id: 2, type: 'youtube', name: '@TechChannel', url: 'https://youtube.com/@techchannel', status: 'active' },
  { id: 3, type: 'github', name: 'nexus-bot', url: 'https://github.com/org/nexus-bot', status: 'inactive' },
]

const typeIcon: Record<string, any> = {
  rss: Rss,
  youtube: Youtube,
  github: Github,
  webhook: Webhook,
  twitter: Twitter,
}

const typeColor: Record<string, string> = {
  rss: 'text-orange-500 bg-orange-500/10',
  youtube: 'text-red-500 bg-red-500/10',
  github: 'text-white bg-white/10',
  webhook: 'text-blue-500 bg-blue-500/10',
  twitter: 'text-sky-500 bg-sky-500/10',
}

export default function Integrations() {
  const { groupId } = useParams<{ groupId: string }>()

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Integrations</h1>
        <p className="text-dark-400 mt-1">
          Connect external services to your group
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Active Feeds"
          value="2"
          icon={Plug}
        />
        <StatCard
          title="Total Integrations"
          value="3"
          icon={Rss}
        />
      </div>

      {/* Available Integration Types */}
      <Card title="Available Integrations" icon={Plug} className="mb-6">
        <div className="grid grid-cols-2 gap-3 mt-4">
          {[
            { type: 'rss', label: 'RSS Feeds', cmd: '/addrss', Icon: Rss },
            { type: 'youtube', label: 'YouTube', cmd: '/addyoutube', Icon: Youtube },
            { type: 'github', label: 'GitHub', cmd: '/addgithub', Icon: Github },
            { type: 'webhook', label: 'Webhooks', cmd: '/addwebhook', Icon: Webhook },
            { type: 'twitter', label: 'Twitter/X', cmd: '/addtwitter', Icon: Twitter },
          ].map(({ type, label, cmd, Icon }) => (
            <div key={type} className={`flex items-center gap-3 rounded-lg p-3 ${typeColor[type] || 'bg-dark-800'}`}>
              <Icon className="w-5 h-5 flex-shrink-0" />
              <div>
                <p className="text-white text-sm font-medium">{label}</p>
                <p className="text-dark-400 text-xs">{cmd}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Active Integrations */}
      <Card title="Configured Integrations" icon={PlusCircle}>
        {mockFeeds.length > 0 ? (
          <div className="space-y-3 mt-4">
            {mockFeeds.map((feed) => {
              const Icon = typeIcon[feed.type] || Plug
              const color = typeColor[feed.type] || 'text-primary-500 bg-primary-500/10'
              return (
                <div key={feed.id} className="flex items-center gap-3 bg-dark-800 rounded-lg p-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium">{feed.name}</p>
                    <p className="text-dark-400 text-xs truncate">{feed.url}</p>
                  </div>
                  <Badge variant={feed.status === 'active' ? 'success' : 'default'}>
                    {feed.status === 'active' ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="mt-4 text-center py-8">
            <Plug className="w-8 h-8 text-dark-600 mx-auto mb-3" />
            <p className="text-dark-400 text-sm">No integrations configured yet</p>
            <p className="text-dark-500 text-xs mt-1">Use commands in the group to add integrations</p>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-dark-700">
          <p className="text-dark-400 text-sm text-center">
            Add integrations with <code className="text-primary-400">/addrss</code>, <code className="text-primary-400">/addyoutube</code>, etc.
          </p>
        </div>
      </Card>
    </div>
  )
}
