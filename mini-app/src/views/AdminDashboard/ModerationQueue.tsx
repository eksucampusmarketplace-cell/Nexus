import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield,
  AlertTriangle,
  Clock,
  Check,
  X,
  User,
  MessageSquare,
  Ban,
  VolumeX,
  Eye,
  RefreshCw,
  Filter,
} from 'lucide-react'
import {
  getModerationQueue,
  resolveModerationAction,
  warnUser,
  muteUser,
  banUser,
  kickUser,
} from '../../api/moderation'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

interface QueueItem {
  id: number
  type: 'message' | 'user' | 'raid'
  severity: 'low' | 'medium' | 'high' | 'critical'
  reason: string
  confidence: number
  message?: {
    id: number
    text: string
    sender: {
      id: number
      username: string
      first_name: string
    }
  }
  user?: {
    id: number
    username: string
    first_name: string
    is_new: boolean
    account_age_days: number
  }
  suggested_action: string
  created_at: string
}

export default function ModerationQueue() {
  const { groupId } = useParams<{ groupId: string }>()
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState<number | null>(null)
  const [filter, setFilter] = useState<string>('all')

  const loadQueue = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const data = await getModerationQueue(parseInt(groupId))
      setQueue(data.items || [])
    } catch (error) {
      toast.error('Failed to load moderation queue')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQueue()
  }, [groupId])

  const handleAction = async (
    item: QueueItem,
    action: 'approve' | 'dismiss' | 'custom',
    customAction?: { type: string; duration?: string; reason?: string }
  ) => {
    if (!groupId) return
    setProcessing(item.id)
    try {
      await resolveModerationAction(parseInt(groupId), item.id, action, customAction)
      setQueue(queue.filter((q) => q.id !== item.id))
      toast.success(action === 'dismiss' ? 'Item dismissed' : 'Action executed')
    } catch (error) {
      toast.error('Failed to process action')
    } finally {
      setProcessing(null)
    }
  }

  const handleQuickAction = async (item: QueueItem, actionType: string) => {
    if (!groupId || !item.user) return
    setProcessing(item.id)
    try {
      switch (actionType) {
        case 'warn':
          await warnUser(parseInt(groupId), item.user.id, item.reason)
          break
        case 'mute':
          await muteUser(parseInt(groupId), item.user.id, '1h', item.reason)
          break
        case 'ban':
          await banUser(parseInt(groupId), item.user.id, '24h', item.reason)
          break
        case 'kick':
          await kickUser(parseInt(groupId), item.user.id, item.reason)
          break
      }
      await resolveModerationAction(parseInt(groupId), item.id, 'approve')
      setQueue(queue.filter((q) => q.id !== item.id))
      toast.success(`User ${actionType}ed`)
    } catch (error) {
      toast.error('Failed to execute action')
    } finally {
      setProcessing(null)
    }
  }

  const filteredQueue =
    filter === 'all' ? queue : queue.filter((item) => item.type === filter)

  const severityColors = {
    low: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Moderation Queue</h1>
          <p className="text-dark-400 mt-1">AI-flagged content requiring attention</p>
        </div>
        <button
          onClick={loadQueue}
          className="p-2 bg-dark-800 rounded-lg hover:bg-dark-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5 text-dark-400" />
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'all', label: 'All', count: queue.length },
          { id: 'message', label: 'Messages', count: queue.filter((q) => q.type === 'message').length },
          { id: 'user', label: 'Users', count: queue.filter((q) => q.type === 'user').length },
          { id: 'raid', label: 'Raid', count: queue.filter((q) => q.type === 'raid').length },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              filter === tab.id
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            {tab.label}
            <span className="ml-2 px-2 py-0.5 bg-dark-900 rounded-full text-xs">{tab.count}</span>
          </button>
        ))}
      </div>

      {/* Queue Items */}
      {filteredQueue.length === 0 ? (
        <div className="text-center py-12">
          <Shield className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-dark-300">All Clear!</h3>
          <p className="text-dark-500">No items in the moderation queue</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredQueue.map((item) => (
            <Card key={item.id} className="border-l-4 border-l-primary-500">
              <div className="flex items-start gap-4">
                <div
                  className={`p-2 rounded-lg ${
                    item.type === 'message'
                      ? 'bg-blue-500/20'
                      : item.type === 'user'
                      ? 'bg-purple-500/20'
                      : 'bg-red-500/20'
                  }`}
                >
                  {item.type === 'message' ? (
                    <MessageSquare className="w-5 h-5 text-blue-400" />
                  ) : item.type === 'user' ? (
                    <User className="w-5 h-5 text-purple-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[item.severity]}`}>
                      {item.severity.toUpperCase()}
                    </span>
                    <span className="text-dark-500 text-xs">
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                    <span className="text-dark-600 text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-white mb-3">{item.reason}</p>

                  {item.message && (
                    <div className="bg-dark-800 rounded-lg p-3 mb-3">
                      <p className="text-dark-400 text-sm line-clamp-2">{item.message.text}</p>
                      <p className="text-dark-500 text-xs mt-2">
                        From: {item.message.sender.first_name}
                        {item.message.sender.username && ` (@${item.message.sender.username})`}
                      </p>
                    </div>
                  )}

                  {item.user && (
                    <div className="flex items-center gap-4 text-sm text-dark-400 mb-3">
                      <span className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        {item.user.first_name}
                        {item.user.username && ` (@${item.user.username})`}
                      </span>
                      {item.user.is_new && (
                        <span className="text-orange-400">New account ({item.user.account_age_days} days)</span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-dark-500 text-xs">Suggested: {item.suggested_action}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-dark-800">
                <button
                  onClick={() => handleAction(item, 'dismiss')}
                  disabled={processing === item.id}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-dark-300 transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  Dismiss
                </button>
                <button
                  onClick={() => handleAction(item, 'approve')}
                  disabled={processing === item.id}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white transition-colors disabled:opacity-50"
                >
                  <Check className="w-4 h-4" />
                  Approve
                </button>
              </div>

              {item.user && (
                <div className="grid grid-cols-4 gap-2 mt-3">
                  <button
                    onClick={() => handleQuickAction(item, 'warn')}
                    disabled={processing === item.id}
                    className="flex items-center justify-center gap-1 px-3 py-2 bg-yellow-600/20 hover:bg-yellow-600/30 rounded-lg text-yellow-400 text-sm transition-colors disabled:opacity-50"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    Warn
                  </button>
                  <button
                    onClick={() => handleQuickAction(item, 'mute')}
                    disabled={processing === item.id}
                    className="flex items-center justify-center gap-1 px-3 py-2 bg-orange-600/20 hover:bg-orange-600/30 rounded-lg text-orange-400 text-sm transition-colors disabled:opacity-50"
                  >
                    <VolumeX className="w-4 h-4" />
                    Mute
                  </button>
                  <button
                    onClick={() => handleQuickAction(item, 'kick')}
                    disabled={processing === item.id}
                    className="flex items-center justify-center gap-1 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 rounded-lg text-red-400 text-sm transition-colors disabled:opacity-50"
                  >
                    <User className="w-4 h-4" />
                    Kick
                  </button>
                  <button
                    onClick={() => handleQuickAction(item, 'ban')}
                    disabled={processing === item.id}
                    className="flex items-center justify-center gap-1 px-3 py-2 bg-red-600/40 hover:bg-red-600/50 rounded-lg text-red-300 text-sm transition-colors disabled:opacity-50"
                  >
                    <Ban className="w-4 h-4" />
                    Ban
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
