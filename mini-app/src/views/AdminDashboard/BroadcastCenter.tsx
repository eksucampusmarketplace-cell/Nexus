import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Megaphone,
  Send,
  Calendar,
  Clock,
  Users,
  Settings,
  Plus,
  Trash2,
  Edit3,
  Eye,
  CheckCircle,
  XCircle,
  Copy,
  BarChart3,
  Hash,
  FileText,
  Image as ImageIcon,
  LayoutTemplate,
  Save,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as broadcastAPI from '../../api/broadcast'

Modal.setAppElement('#root')

type TabType = 'broadcasts' | 'channels' | 'templates' | 'stats'
type TargetType = 'all' | 'role' | 'active' | 'inactive' | 'custom'

export default function BroadcastCenter() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('broadcasts')
  const [broadcasts, setBroadcasts] = useState<broadcastAPI.BroadcastMessage[]>([])
  const [channels, setChannels] = useState<broadcastAPI.ChannelConfig[]>([])
  const [templates, setTemplates] = useState<broadcastAPI.MessageTemplate[]>([])
  const [stats, setStats] = useState<broadcastAPI.BroadcastStats | null>(null)
  
  // Modal states
  const [broadcastModalOpen, setBroadcastModalOpen] = useState(false)
  const [channelModalOpen, setChannelModalOpen] = useState(false)
  const [templateModalOpen, setTemplateModalOpen] = useState(false)
  const [previewModalOpen, setPreviewModalOpen] = useState(false)
  
  // Form states
  const [broadcastForm, setBroadcastForm] = useState({
    content: '',
    target_type: 'all' as TargetType,
    target_filter: {},
    scheduled_at: '',
    media_file_id: '',
    button_data: null as any
  })
  const [channelForm, setChannelForm] = useState({
    channel_id: '',
    channel_name: '',
    channel_username: '',
    channel_type: 'announcement' as const,
    auto_post_enabled: false,
    format_template: '',
    include_source: true,
    include_media: true
  })
  const [templateForm, setTemplateForm] = useState({
    name: '',
    content: '',
    category: 'announcement' as const,
    variables: [] as string[]
  })
  const [selectedBroadcast, setSelectedBroadcast] = useState<broadcastAPI.BroadcastMessage | null>(null)

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'broadcasts':
          const broadcastsRes = await broadcastAPI.getBroadcasts(parseInt(groupId))
          setBroadcasts(broadcastsRes)
          break
        case 'channels':
          const channelsRes = await broadcastAPI.getChannelConfigs(parseInt(groupId))
          setChannels(channelsRes)
          break
        case 'templates':
          const templatesRes = await broadcastAPI.getMessageTemplates(parseInt(groupId))
          setTemplates(templatesRes)
          break
        case 'stats':
          const statsRes = await broadcastAPI.getBroadcastStats(parseInt(groupId))
          setStats(statsRes)
          break
      }
    } catch (error) {
      console.error('Failed to load broadcast data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBroadcast = async () => {
    if (!groupId || !broadcastForm.content) return
    try {
      await broadcastAPI.createBroadcast(parseInt(groupId), broadcastForm)
      toast.success(broadcastForm.scheduled_at ? 'Broadcast scheduled!' : 'Broadcast sent!')
      setBroadcastModalOpen(false)
      setBroadcastForm({
        content: '',
        target_type: 'all',
        target_filter: {},
        scheduled_at: '',
        media_file_id: '',
        button_data: null
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create broadcast')
    }
  }

  const handleAddChannel = async () => {
    if (!groupId || !channelForm.channel_id || !channelForm.channel_name) return
    try {
      await broadcastAPI.addChannel(parseInt(groupId), {
        ...channelForm,
        channel_id: parseInt(channelForm.channel_id)
      })
      toast.success('Channel added!')
      setChannelModalOpen(false)
      setChannelForm({
        channel_id: '',
        channel_name: '',
        channel_username: '',
        channel_type: 'announcement',
        auto_post_enabled: false,
        format_template: '',
        include_source: true,
        include_media: true
      })
      loadData()
    } catch (error) {
      toast.error('Failed to add channel')
    }
  }

  const handleCreateTemplate = async () => {
    if (!groupId || !templateForm.name || !templateForm.content) return
    try {
      await broadcastAPI.createMessageTemplate(parseInt(groupId), templateForm)
      toast.success('Template created!')
      setTemplateModalOpen(false)
      setTemplateForm({
        name: '',
        content: '',
        category: 'announcement',
        variables: []
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create template')
    }
  }

  const handleCancelBroadcast = async (broadcastId: number) => {
    if (!groupId) return
    try {
      await broadcastAPI.cancelBroadcast(parseInt(groupId), broadcastId)
      toast.success('Broadcast cancelled')
      loadData()
    } catch (error) {
      toast.error('Failed to cancel')
    }
  }

  const handleDeleteBroadcast = async (broadcastId: number) => {
    if (!groupId || !confirm('Delete this broadcast?')) return
    try {
      await broadcastAPI.deleteBroadcast(parseInt(groupId), broadcastId)
      toast.success('Broadcast deleted')
      loadData()
    } catch (error) {
      toast.error('Failed to delete')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'bg-green-500/20 text-green-400'
      case 'scheduled': return 'bg-blue-500/20 text-blue-400'
      case 'sending': return 'bg-yellow-500/20 text-yellow-400'
      case 'failed': return 'bg-red-500/20 text-red-400'
      default: return 'bg-dark-700 text-dark-400'
    }
  }

  if (loading && !broadcasts.length) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl flex items-center justify-center">
            <Megaphone className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Broadcast Center</h1>
            <p className="text-dark-400 mt-1">Mass messaging, announcements, and channel posting</p>
          </div>
        </div>
        <button
          onClick={() => setBroadcastModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors"
        >
          <Send className="w-4 h-4" />
          New Broadcast
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'broadcasts', label: 'Broadcasts', icon: Megaphone },
          { id: 'channels', label: 'Channels', icon: Hash },
          { id: 'templates', label: 'Templates', icon: LayoutTemplate },
          { id: 'stats', label: 'Statistics', icon: BarChart3 },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Broadcasts Tab */}
      {activeTab === 'broadcasts' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {broadcasts.length === 0 ? (
              <Card className="md:col-span-2">
                <div className="text-center py-12">
                  <Megaphone className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No broadcasts yet</p>
                  <button
                    onClick={() => setBroadcastModalOpen(true)}
                    className="text-primary-400 hover:text-primary-300 mt-2"
                  >
                    Create your first broadcast
                  </button>
                </div>
              </Card>
            ) : (
              broadcasts.map(broadcast => (
                <Card key={broadcast.id} className="hover:border-dark-700 transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(broadcast.status)}`}>
                        {broadcast.status}
                      </span>
                      {broadcast.scheduled_at && (
                        <span className="px-2 py-0.5 bg-purple-500/20 rounded text-xs text-purple-400">
                          <Clock className="w-3 h-3 inline mr-1" />
                          Scheduled
                        </span>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => {
                          setSelectedBroadcast(broadcast)
                          setPreviewModalOpen(true)
                        }}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Eye className="w-4 h-4 text-dark-400" />
                      </button>
                      {broadcast.status === 'scheduled' && (
                        <button
                          onClick={() => handleCancelBroadcast(broadcast.id)}
                          className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                        >
                          <XCircle className="w-4 h-4 text-yellow-400" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteBroadcast(broadcast.id)}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                  </div>

                  <p className="text-white line-clamp-3 mb-4">{broadcast.content}</p>

                  <div className="flex flex-wrap gap-4 text-sm text-dark-400">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      Target: {broadcast.target_type}
                    </span>
                    {broadcast.sent_count > 0 && (
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        {broadcast.sent_count} sent
                      </span>
                    )}
                    {broadcast.failed_count > 0 && (
                      <span className="flex items-center gap-1">
                        <XCircle className="w-4 h-4 text-red-400" />
                        {broadcast.failed_count} failed
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(broadcast.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Channels Tab */}
      {activeTab === 'channels' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Connected Channels</h3>
            <button
              onClick={() => setChannelModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Channel
            </button>
          </div>

          <div className="grid gap-4">
            {channels.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <Hash className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No channels connected</p>
                  <p className="text-sm text-dark-500 mt-1">Add channels to auto-post updates</p>
                </div>
              </Card>
            ) : (
              channels.map(channel => (
                <Card key={channel.id} className="hover:border-dark-700 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl flex items-center justify-center">
                        <Hash className="w-6 h-6 text-blue-400" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-white">{channel.channel_name}</h4>
                        <div className="flex items-center gap-2 mt-1 text-sm text-dark-400">
                          <span className="px-2 py-0.5 bg-dark-800 rounded text-xs">{channel.channel_type}</span>
                          {channel.channel_username && (
                            <span>@{channel.channel_username}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`w-2 h-2 rounded-full ${channel.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-sm text-dark-400">{channel.is_active ? 'Active' : 'Inactive'}</span>
                      </div>
                      <p className="text-sm text-dark-500">{channel.total_posts} posts</p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Message Templates</h3>
            <button
              onClick={() => setTemplateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Template
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.length === 0 ? (
              <Card className="md:col-span-2">
                <div className="text-center py-12">
                  <LayoutTemplate className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No templates yet</p>
                  <p className="text-sm text-dark-500 mt-1">Create templates for common messages</p>
                </div>
              </Card>
            ) : (
              templates.map(template => (
                <Card key={template.id} className="hover:border-dark-700 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-white">{template.name}</h4>
                      <span className="px-2 py-0.5 bg-dark-800 rounded text-xs text-dark-400">
                        {template.category}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setBroadcastForm(prev => ({ ...prev, content: template.content }))
                        setBroadcastModalOpen(true)
                      }}
                      className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    >
                      <Copy className="w-4 h-4 text-primary-400" />
                    </button>
                  </div>
                  <p className="text-dark-400 text-sm line-clamp-3">{template.content}</p>
                  {template.variables.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                      {template.variables.map(v => (
                        <span key={v} className="px-2 py-0.5 bg-primary-500/10 rounded text-xs text-primary-400">
                          {'{'}{v}{'}'}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Total Broadcasts" value={stats.total_broadcasts} icon={Megaphone} />
            <StatCard title="Total Sent" value={stats.total_sent} icon={CheckCircle} />
            <StatCard title="Total Failed" value={stats.total_failed} icon={XCircle} />
            <StatCard title="Avg Open Rate" value={`${stats.average_open_rate}%`} icon={Eye} />
          </div>

          <Card title="Recent Broadcasts" icon={Clock}>
            <div className="space-y-3 mt-4">
              {stats.recent_broadcasts.map((broadcast: broadcastAPI.BroadcastMessage) => (
                <div key={broadcast.id} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                  <div className="flex-1 min-w-0">
                    <p className="text-white truncate">{broadcast.content.slice(0, 50)}...</p>
                    <p className="text-sm text-dark-400">
                      {broadcast.sent_count} sent • {broadcast.failed_count} failed
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(broadcast.status)}`}>
                    {broadcast.status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Create Broadcast Modal */}
      <Modal
        isOpen={broadcastModalOpen}
        onRequestClose={() => setBroadcastModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">New Broadcast</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Message</label>
              <textarea
                value={broadcastForm.content}
                onChange={(e) => setBroadcastForm(prev => ({ ...prev, content: e.target.value }))}
                placeholder="What do you want to broadcast?"
                rows={4}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Target Audience</label>
              <select
                value={broadcastForm.target_type}
                onChange={(e) => setBroadcastForm(prev => ({ ...prev, target_type: e.target.value as TargetType }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="all">All Members</option>
                <option value="active">Active Members</option>
                <option value="inactive">Inactive Members</option>
                <option value="role">By Role</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Schedule (optional)</label>
              <input
                type="datetime-local"
                value={broadcastForm.scheduled_at}
                onChange={(e) => setBroadcastForm(prev => ({ ...prev, scheduled_at: e.target.value }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              />
              <p className="text-xs text-dark-500 mt-1">Leave empty to send immediately</p>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setBroadcastModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateBroadcast}
              disabled={!broadcastForm.content}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              {broadcastForm.scheduled_at ? 'Schedule' : 'Send Now'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Add Channel Modal */}
      <Modal
        isOpen={channelModalOpen}
        onRequestClose={() => setChannelModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Add Channel</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Channel ID</label>
              <input
                type="number"
                value={channelForm.channel_id}
                onChange={(e) => setChannelForm(prev => ({ ...prev, channel_id: e.target.value }))}
                placeholder="Enter channel ID"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Channel Name</label>
              <input
                type="text"
                value={channelForm.channel_name}
                onChange={(e) => setChannelForm(prev => ({ ...prev, channel_name: e.target.value }))}
                placeholder="Display name"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Username (optional)</label>
              <input
                type="text"
                value={channelForm.channel_username}
                onChange={(e) => setChannelForm(prev => ({ ...prev, channel_username: e.target.value }))}
                placeholder="@channelname"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Channel Type</label>
              <select
                value={channelForm.channel_type}
                onChange={(e) => setChannelForm(prev => ({ ...prev, channel_type: e.target.value as any }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="announcement">Announcement</option>
                <option value="updates">Updates</option>
                <option value="moderation">Moderation</option>
                <option value="general">General</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setChannelModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAddChannel}
              disabled={!channelForm.channel_id || !channelForm.channel_name}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Add Channel
            </button>
          </div>
        </div>
      </Modal>

      {/* Create Template Modal */}
      <Modal
        isOpen={templateModalOpen}
        onRequestClose={() => setTemplateModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">New Template</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Template Name</label>
              <input
                type="text"
                value={templateForm.name}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Welcome Message"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Category</label>
              <select
                value={templateForm.category}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, category: e.target.value as any }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="welcome">Welcome</option>
                <option value="rules">Rules</option>
                <option value="announcement">Announcement</option>
                <option value="moderation">Moderation</option>
                <option value="fun">Fun</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Content</label>
              <textarea
                value={templateForm.content}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Template content... Use {variable} for dynamic content"
                rows={4}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setTemplateModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTemplate}
              disabled={!templateForm.name || !templateForm.content}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Template
            </button>
          </div>
        </div>
      </Modal>

      {/* Preview Modal */}
      <Modal
        isOpen={previewModalOpen}
        onRequestClose={() => setPreviewModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-4">Broadcast Preview</h2>
          
          {selectedBroadcast && (
            <div className="bg-dark-800 rounded-xl p-4 mb-6">
              <p className="text-white whitespace-pre-wrap">{selectedBroadcast.content}</p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => setPreviewModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
