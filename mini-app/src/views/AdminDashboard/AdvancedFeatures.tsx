import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Globe, Download, Upload, Play, Pause, Trash2, Plus,
  Settings, ChevronRight, ExternalLink, RefreshCw,
  FileText, Image, Video, MessageSquare, Hash, Users,
  Calendar, Filter, Zap, ArrowRight, Check, X, Copy,
  Scissors, Forward, Database, BookOpen, Clock
} from 'lucide-react'

interface ScrapingJob {
  id: number
  name: string
  description?: string
  target_url: string
  selector?: string
  method: string
  schedule_type: string
  is_active: boolean
  last_run?: string
  last_error?: string
}

interface ChannelConfig {
  id: number
  channel_name: string
  channel_username?: string
  channel_type: string
  auto_post_enabled: boolean
  is_active: boolean
  total_posts: number
}

interface AutoForward {
  id: number
  source_chat_id: number
  dest_chat_id: number
  forward_type: string
  is_active: boolean
  total_forwarded: number
}

interface AdvancedExport {
  id: number
  name: string
  export_type: string
  data_sources: string[]
  format: string
  schedule_enabled: boolean
  last_run?: string
  last_status?: string
}

export default function AdvancedFeatures() {
  const [activeTab, setActiveTab] = useState<'scraping' | 'channels' | 'forwards' | 'exports'>('scraping')
  const [scrapingJobs, setScrapingJobs] = useState<ScrapingJob[]>([])
  const [channels, setChannels] = useState<ChannelConfig[]>([])
  const [forwards, setForwards] = useState<AutoForward[]>([])
  const [exports, setExports] = useState<AdvancedExport[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [scrapingRes, channelsRes, forwardsRes, exportsRes] = await Promise.all([
        fetch('/api/v1/advanced/scraping'),
        fetch('/api/v1/advanced/channels'),
        fetch('/api/v1/advanced/forwards'),
        fetch('/api/v1/advanced/exports')
      ])
      
      setScrapingJobs((await scrapingRes.json()).items || [])
      setChannels((await channelsRes.json()).items || [])
      setForwards((await forwardsRes.json()).items || [])
      setExports((await exportsRes.json()).items || [])
    } catch (error) {
      console.error('Error loading data:', error)
    }
    setLoading(false)
  }

  const runScrapingJob = async (jobId: number) => {
    try {
      const response = await fetch(`/api/v1/advanced/scraping/${jobId}/run`, { method: 'POST' })
      const result = await response.json()
      // Update the job in state
      setScrapingJobs(prev => prev.map(j => 
        j.id === jobId ? { ...j, last_run: new Date().toISOString(), last_error: undefined } : j
      ))
    } catch (error) {
      console.error('Error running scraping job:', error)
    }
  }

  const toggleScrapingJob = async (jobId: number, isActive: boolean) => {
    try {
      await fetch(`/api/v1/advanced/scraping/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !isActive })
      })
      setScrapingJobs(prev => prev.map(j => 
        j.id === jobId ? { ...j, is_active: !isActive } : j
      ))
    } catch (error) {
      console.error('Error toggling job:', error)
    }
  }

  const deleteScrapingJob = async (jobId: number) => {
    if (!confirm('Delete this scraping job?')) return
    try {
      await fetch(`/api/v1/advanced/scraping/${jobId}`, { method: 'DELETE' })
      setScrapingJobs(prev => prev.filter(j => j.id !== jobId))
    } catch (error) {
      console.error('Error deleting job:', error)
    }
  }

  const toggleChannel = async (channelId: number, isActive: boolean) => {
    try {
      await fetch(`/api/v1/advanced/channels/${channelId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !isActive })
      })
      setChannels(prev => prev.map(c => 
        c.id === channelId ? { ...c, is_active: !isActive } : c
      ))
    } catch (error) {
      console.error('Error toggling channel:', error)
    }
  }

  const deleteChannel = async (channelId: number) => {
    if (!confirm('Remove this channel?')) return
    try {
      await fetch(`/api/v1/advanced/channels/${channelId}`, { method: 'DELETE' })
      setChannels(prev => prev.filter(c => c.id !== channelId))
    } catch (error) {
      console.error('Error deleting channel:', error)
    }
  }

  const toggleForward = async (forwardId: number, isActive: boolean) => {
    try {
      await fetch(`/api/v1/advanced/forwards/${forwardId}/toggle`, { method: 'POST' })
      setForwards(prev => prev.map(f => 
        f.id === forwardId ? { ...f, is_active: !isActive } : f
      ))
    } catch (error) {
      console.error('Error toggling forward:', error)
    }
  }

  const deleteForward = async (forwardId: number) => {
    if (!confirm('Delete this forward rule?')) return
    try {
      await fetch(`/api/v1/advanced/forwards/${forwardId}`, { method: 'DELETE' })
      setForwards(prev => prev.filter(f => f.id !== forwardId))
    } catch (error) {
      console.error('Error deleting forward:', error)
    }
  }

  const runExport = async (exportId: number) => {
    try {
      await fetch(`/api/v1/advanced/exports/${exportId}/run`, { method: 'POST' })
      setExports(prev => prev.map(e => 
        e.id === exportId ? { ...e, last_run: new Date().toISOString(), last_status: 'running' } : e
      ))
    } catch (error) {
      console.error('Error running export:', error)
    }
  }

  const deleteExport = async (exportId: number) => {
    if (!confirm('Delete this export configuration?')) return
    try {
      await fetch(`/api/v1/advanced/exports/${exportId}`, { method: 'DELETE' })
      setExports(prev => prev.filter(e => e.id !== exportId))
    } catch (error) {
      console.error('Error deleting export:', error)
    }
  }

  const tabs = [
    { id: 'scraping', label: 'Web Scraping', icon: Scissors },
    { id: 'channels', label: 'Channels', icon: Forward },
    { id: 'forwards', label: 'Auto Forward', icon: ArrowRight },
    { id: 'exports', label: 'Exports', icon: Download },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-accent-600/20 via-secondary-500/20 to-primary-500/20 border-b border-white/5">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHptMCAzMmMtNy43MzIgMC0xNC02LjI2OC0xNC0xNHM2LjI2OC0xNCAxNC0xNCAxNCA2LjI2OCAxNCAxNC02LjI2OCAxNC0xNCAxNHoiIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjAyIi8+PC9nPjwvc3ZnPg==')] opacity-30" />
        <div className="relative max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-accent-400 via-secondary-400 to-primary-400 bg-clip-text text-transparent">
                Advanced Features
              </h1>
              <p className="text-dark-400 mt-2">Web scraping, channel management, and data exports</p>
            </div>
            <button
              onClick={() => setShowCreateModal(activeTab)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-accent-500 to-secondary-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
              <Plus size={20} />
              Add New
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex gap-2 mt-6 overflow-x-auto pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white/10 text-white'
                    : 'text-dark-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <tab.icon size={18} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-64"
            >
              <div className="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
            </motion.div>
          ) : (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {activeTab === 'scraping' && (
                <ScrapingTab 
                  jobs={scrapingJobs}
                  onRun={runScrapingJob}
                  onToggle={toggleScrapingJob}
                  onDelete={deleteScrapingJob}
                />
              )}
              {activeTab === 'channels' && (
                <ChannelsTab 
                  channels={channels}
                  onToggle={toggleChannel}
                  onDelete={deleteChannel}
                />
              )}
              {activeTab === 'forwards' && (
                <ForwardsTab 
                  forwards={forwards}
                  onToggle={toggleForward}
                  onDelete={deleteForward}
                />
              )}
              {activeTab === 'exports' && (
                <ExportsTab 
                  exports={exports}
                  onRun={runExport}
                  onDelete={deleteExport}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Quick Export Panel */}
      {activeTab === 'exports' && (
        <QuickExportPanel />
      )}
    </div>
  )
}

function ScrapingTab({ jobs, onRun, onToggle, onDelete }: {
  jobs: ScrapingJob[]
  onRun: (id: number) => void
  onToggle: (id: number, active: boolean) => void
  onDelete: (id: number) => void
}) {
  if (jobs.length === 0) {
    return (
      <EmptyState 
        icon={Scissors}
        title="No scraping jobs"
        description="Create a job to automatically scrape data from websites"
      />
    )
  }

  return (
    <div className="space-y-4">
      {jobs.map(job => (
        <motion.div
          key={job.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-accent-500/30 transition-colors"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                job.is_active ? 'bg-accent-500/20' : 'bg-dark-700'
              }`}>
                <Globe size={24} className={job.is_active ? 'text-accent-400' : 'text-dark-400'} />
              </div>
              <div>
                <h3 className="font-semibold text-white">{job.name}</h3>
                <p className="text-sm text-dark-400 flex items-center gap-2 mt-1">
                  <ExternalLink size={14} />
                  {job.target_url}
                </p>
                {job.selector && (
                  <p className="text-xs text-dark-500 mt-1">
                    Selector: <code className="bg-dark-800 px-1 rounded">{job.selector}</code>
                  </p>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => onRun(job.id)}
                className="p-2 rounded-lg text-accent-400 hover:bg-accent-400/10 transition-colors"
                title="Run now"
              >
                <Play size={18} />
              </button>
              <button
                onClick={() => onToggle(job.id, job.is_active)}
                className={`p-2 rounded-lg transition-colors ${
                  job.is_active 
                    ? 'text-green-400 hover:bg-green-400/10' 
                    : 'text-dark-400 hover:bg-dark-700'
                }`}
                title={job.is_active ? 'Pause' : 'Resume'}
              >
                {job.is_active ? <Pause size={18} /> : <Play size={18} />}
              </button>
              <button
                onClick={() => onDelete(job.id)}
                className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/5">
            <div className="flex items-center gap-4 text-sm">
              <span className="text-dark-500">
                Method: <span className="text-white">{job.method}</span>
              </span>
              <span className="text-dark-500">
                Schedule: <span className="text-white">{job.schedule_type}</span>
              </span>
              {job.last_run && (
                <span className="text-dark-500">
                  Last run: <span className="text-white">{new Date(job.last_run).toLocaleString()}</span>
                </span>
              )}
            </div>
            {job.last_error && (
              <span className="text-xs text-red-400">Error: {job.last_error}</span>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function ChannelsTab({ channels, onToggle, onDelete }: {
  channels: ChannelConfig[]
  onToggle: (id: number, active: boolean) => void
  onDelete: (id: number) => void
}) {
  if (channels.length === 0) {
    return (
      <EmptyState 
        icon={Forward}
        title="No channels configured"
        description="Add channels to automatically post content"
      />
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {channels.map(channel => (
        <motion.div
          key={channel.id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-secondary-500/30 transition-colors"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                channel.is_active ? 'bg-secondary-500/20' : 'bg-dark-700'
              }`}>
                <Forward size={24} className={channel.is_active ? 'text-secondary-400' : 'text-dark-400'} />
              </div>
              <div>
                <h3 className="font-semibold text-white">{channel.channel_name}</h3>
                {channel.channel_username && (
                  <p className="text-sm text-dark-400">@{channel.channel_username}</p>
                )}
              </div>
            </div>
            <button
              onClick={() => onDelete(channel.id)}
              className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
            >
              <Trash2 size={18} />
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                channel.is_active 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-dark-700 text-dark-400'
              }`}>
                {channel.is_active ? 'Active' : 'Inactive'}
              </span>
              <span className="px-2 py-1 bg-dark-700 text-dark-400 text-xs rounded-md">
                {channel.channel_type}
              </span>
            </div>
            <span className="text-sm text-dark-500">
              {channel.total_posts} posts
            </span>
          </div>
          
          {channel.auto_post_enabled && (
            <div className="mt-3 pt-3 border-t border-white/5">
              <span className="text-xs text-accent-400 flex items-center gap-1">
                <Zap size={12} />
                Auto-post enabled
              </span>
            </div>
          )}
        </motion.div>
      ))}
    </div>
  )
}

function ForwardsTab({ forwards, onToggle, onDelete }: {
  forwards: AutoForward[]
  onToggle: (id: number, active: boolean) => void
  onDelete: (id: number) => void
}) {
  if (forwards.length === 0) {
    return (
      <EmptyState 
        icon={ArrowRight}
        title="No forward rules"
        description="Create rules to automatically forward messages between chats"
      />
    )
  }

  return (
    <div className="space-y-4">
      {forwards.map(forward => (
        <motion.div
          key={forward.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-dark-700 flex items-center justify-center">
              <ChevronRight size={20} className="text-dark-400" />
            </div>
            <div>
              <p className="text-white">
                {forward.source_chat_id} → {forward.dest_chat_id}
              </p>
              <p className="text-sm text-dark-400">
                Type: {forward.forward_type} • {forward.total_forwarded} forwarded
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => onToggle(forward.id, forward.is_active)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                forward.is_active 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-dark-700 text-dark-400'
              }`}
            >
              {forward.is_active ? 'Active' : 'Paused'}
            </button>
            <button
              onClick={() => onDelete(forward.id)}
              className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
            >
              <Trash2 size={18} />
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function ExportsTab({ exports, onRun, onDelete }: {
  exports: AdvancedExport[]
  onRun: (id: number) => void
  onDelete: (id: number) => void
}) {
  if (exports.length === 0) {
    return (
      <EmptyState 
        icon={Download}
        title="No export configurations"
        description="Set up automated exports of your group data"
      />
    )
  }

  return (
    <div className="space-y-4">
      {exports.map(exp => (
        <motion.div
          key={exp.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/5 border border-white/10 rounded-xl p-4"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center">
                <Database size={24} className="text-primary-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{exp.name}</h3>
                <p className="text-sm text-dark-400 mt-1">
                  {exp.export_type} • {exp.format.toUpperCase()}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {exp.data_sources.map((source, i) => (
                    <span key={i} className="px-2 py-0.5 bg-dark-700 text-dark-400 text-xs rounded">
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => onRun(exp.id)}
                className="p-2 rounded-lg text-primary-400 hover:bg-primary-400/10 transition-colors"
              >
                <Play size={18} />
              </button>
              <button
                onClick={() => onDelete(exp.id)}
                className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
          
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-white/5 text-sm">
            {exp.schedule_enabled && (
              <span className="text-dark-500 flex items-center gap-1">
                <Clock size={14} />
                Scheduled
              </span>
            )}
            {exp.last_run && (
              <span className="text-dark-500">
                Last: {new Date(exp.last_run).toLocaleString()}
              </span>
            )}
            {exp.last_status && (
              <span className={`px-2 py-0.5 rounded text-xs ${
                exp.last_status === 'completed' 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {exp.last_status}
              </span>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function QuickExportPanel() {
  const [exporting, setExporting] = useState<string | null>(null)
  const [exportTypes, setExportTypes] = useState<any>({})

  useEffect(() => {
    fetch('/api/v1/advanced/quick-export/types')
      .then(res => res.json())
      .then(setExportTypes)
  }, [])

  const quickExport = async (type: string) => {
    setExporting(type)
    try {
      // Trigger export
      await new Promise(resolve => setTimeout(resolve, 2000))
    } catch (error) {
      console.error('Export error:', error)
    }
    setExporting(null)
  }

  const exportTypeList = [
    { key: 'members', icon: Users, color: 'from-blue-500 to-cyan-500' },
    { key: 'messages', icon: MessageSquare, color: 'from-green-500 to-emerald-500' },
    { key: 'notes', icon: BookOpen, color: 'from-yellow-500 to-orange-500' },
    { key: 'filters', icon: Filter, color: 'from-purple-500 to-pink-500' },
    { key: 'full', icon: Database, color: 'from-primary-500 to-accent-500' },
  ]

  return (
    <div className="mt-12">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Zap size={20} className="text-accent-400" />
        Quick Export
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {exportTypeList.map(({ key, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => quickExport(key)}
            disabled={!!exporting}
            className={`p-4 bg-gradient-to-br ${color} rounded-xl text-white font-medium hover:opacity-90 disabled:opacity-50 transition-all hover:scale-105`}
          >
            <Icon size={24} className="mx-auto mb-2" />
            {exportTypes[key]?.name || key}
          </button>
        ))}
      </div>
    </div>
  )
}

function EmptyState({ icon: Icon, title, description }: {
  icon: any
  title: string
  description: string
}) {
  return (
    <div className="text-center py-16">
      <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
        <Icon size={40} className="text-primary-400" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-dark-400">{description}</p>
    </div>
  )
}
