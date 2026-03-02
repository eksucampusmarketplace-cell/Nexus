import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Skull, RefreshCw, Trash2, Filter, Search, ChevronLeft, ChevronRight, AlertTriangle, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  getGraveyardMessages,
  getGraveyardStats,
  restoreMessage,
  purgeMessage,
  type DeletedMessage,
  type GraveyardStats,
  type GraveyardFilters,
} from '../../api/graveyard'

export default function Graveyard() {
  const { groupId } = useParams<{ groupId: string }>()
  const [messages, setMessages] = useState<DeletedMessage[]>([])
  const [stats, setStats] = useState<GraveyardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [filters, setFilters] = useState({
    deletion_reason: '',
    content_type: '',
    restored: '',
    search: '',
  })
  const [showFilters, setShowFilters] = useState(false)
  const [selectedMessage, setSelectedMessage] = useState<DeletedMessage | null>(null)
  const [restoring, setRestoring] = useState<number | null>(null)

  useEffect(() => {
    if (groupId) {
      fetchMessages()
      fetchStats()
    }
  }, [groupId, page, filters])

  const fetchMessages = async () => {
    try {
      setLoading(true)
      const response = await getGraveyardMessages(
        parseInt(groupId!),
        page,
        20,
        {
          deletion_reason: filters.deletion_reason || undefined,
          content_type: filters.content_type || undefined,
          restored: filters.restored === '' ? undefined : filters.restored === 'true',
        }
      )
      setMessages(response.items)
      setTotal(response.total)
      setHasMore(response.has_more)
    } catch (error) {
      console.error('Error fetching graveyard:', error)
      toast.error('Failed to load deleted messages')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await getGraveyardStats(parseInt(groupId!))
      setStats(response)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleRestore = async (messageId: number) => {
    if (!confirm('Are you sure you want to restore this message? It will be re-sent to the group.')) {
      return
    }

    try {
      setRestoring(messageId)
      await restoreMessage(parseInt(groupId!), messageId)
      toast.success('Message restored successfully')
      fetchMessages()
      fetchStats()
    } catch (error: any) {
      console.error('Error restoring message:', error)
      toast.error(error.response?.data?.detail || 'Failed to restore message')
    } finally {
      setRestoring(null)
    }
  }

  const handlePurge = async (messageId: number) => {
    if (!confirm('Are you sure you want to permanently delete this message? This cannot be undone.')) {
      return
    }

    try {
      await purgeMessage(parseInt(groupId!), messageId)
      toast.success('Message purged from graveyard')
      fetchMessages()
      fetchStats()
    } catch (error: any) {
      console.error('Error purging message:', error)
      toast.error(error.response?.data?.detail || 'Failed to purge message')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const getReasonBadgeColor = (reason: string) => {
    const colors: Record<string, string> = {
      word_filter: 'bg-red-500/20 text-red-400',
      flood: 'bg-yellow-500/20 text-yellow-400',
      lock_violation: 'bg-orange-500/20 text-orange-400',
      nsfw: 'bg-pink-500/20 text-pink-400',
      spam: 'bg-purple-500/20 text-purple-400',
      ai_moderation: 'bg-blue-500/20 text-blue-400',
      manual: 'bg-gray-500/20 text-gray-400',
    }
    return colors[reason] || 'bg-gray-500/20 text-gray-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Skull className="w-6 h-6" />
            Message Graveyard
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            Review and restore deleted messages
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
            showFilters ? 'bg-blue-500 text-white' : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <p className="text-dark-400 text-sm">Total Deleted</p>
            <p className="text-2xl font-bold text-white">{stats.total_deleted}</p>
          </div>
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <p className="text-dark-400 text-sm">Last 24h</p>
            <p className="text-2xl font-bold text-yellow-400">{stats.recent_deletions_24h}</p>
          </div>
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <p className="text-dark-400 text-sm">Restored</p>
            <p className="text-2xl font-bold text-green-400">{stats.restored_count}</p>
          </div>
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <p className="text-dark-400 text-sm">Restore Rate</p>
            <p className="text-2xl font-bold text-blue-400">{stats.restoration_rate.toFixed(1)}%</p>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-dark-400 mb-1">Deletion Reason</label>
              <select
                value={filters.deletion_reason}
                onChange={(e) => setFilters({ ...filters, deletion_reason: e.target.value })}
                className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Reasons</option>
                <option value="word_filter">Word Filter</option>
                <option value="flood">Flood</option>
                <option value="lock_violation">Lock Violation</option>
                <option value="nsfw">NSFW</option>
                <option value="spam">Spam</option>
                <option value="ai_moderation">AI Moderation</option>
                <option value="manual">Manual</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-400 mb-1">Content Type</label>
              <select
                value={filters.content_type}
                onChange={(e) => setFilters({ ...filters, content_type: e.target.value })}
                className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white"
              >
                <option value="">All Types</option>
                <option value="text">Text</option>
                <option value="photo">Photo</option>
                <option value="video">Video</option>
                <option value="sticker">Sticker</option>
                <option value="gif">GIF</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-400 mb-1">Restoration Status</label>
              <select
                value={filters.restored}
                onChange={(e) => setFilters({ ...filters, restored: e.target.value })}
                className="w-full bg-dark-700 border border-dark-600 rounded px-3 py-2 text-white"
              >
                <option value="">All</option>
                <option value="false">Not Restored</option>
                <option value="true">Restored</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilters({ deletion_reason: '', content_type: '', restored: '', search: '' })
                  setPage(1)
                }}
                className="w-full bg-dark-600 hover:bg-dark-500 text-white px-4 py-2 rounded"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages List */}
      <div className="bg-dark-800 rounded-lg border border-dark-700">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-dark-400">
            <Skull className="w-12 h-12 mb-4 opacity-50" />
            <p>No deleted messages found</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-700">
            {messages.map((msg) => (
              <div key={msg.id} className="p-4 hover:bg-dark-750">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* User Info */}
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 rounded-full bg-dark-600 flex items-center justify-center">
                        <span className="text-sm font-medium text-white">
                          {(msg.user_first_name || msg.user_username || 'U')[0].toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          {msg.user_first_name} {msg.user_last_name}
                        </p>
                        {msg.user_username && (
                          <p className="text-dark-400 text-sm">@{msg.user_username}</p>
                        )}
                      </div>
                    </div>

                    {/* Content Preview */}
                    {msg.content && (
                      <div className="bg-dark-900 rounded p-3 mb-2 border border-dark-700">
                        <p className="text-gray-300 text-sm break-words">
                          {msg.content.length > 200 ? `${msg.content.substring(0, 200)}...` : msg.content}
                        </p>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <span className={`px-2 py-1 rounded ${getReasonBadgeColor(msg.deletion_reason)}`}>
                        {msg.deletion_reason.replace('_', ' ')}
                      </span>
                      <span className="text-dark-400">
                        {formatDate(msg.deleted_at)}
                      </span>
                      {msg.trigger_word && (
                        <span className="text-dark-400">
                          • Trigger: <span className="text-red-400">{msg.trigger_word}</span>
                        </span>
                      )}
                      {msg.restored_at && (
                        <span className="flex items-center gap-1 text-green-400">
                          <Check className="w-3 h-3" />
                          Restored
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    {msg.can_restore && !msg.restored_at && (
                      <button
                        onClick={() => handleRestore(msg.id)}
                        disabled={restoring === msg.id}
                        className="p-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-50"
                        title="Restore message"
                      >
                        {restoring === msg.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <RefreshCw className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedMessage(msg)}
                      className="p-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg"
                      title="View details"
                    >
                      <Search className="w-4 h-4" />
                    </button>
                    {!msg.restored_at && (
                      <button
                        onClick={() => handlePurge(msg.id)}
                        className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg"
                        title="Permanently delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > 20 && (
          <div className="flex items-center justify-between p-4 border-t border-dark-700">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="flex items-center gap-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-dark-400">
              Page {page} of {Math.ceil(total / 20)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!hasMore}
              className="flex items-center gap-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Message Detail Modal */}
      {selectedMessage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto border border-dark-700">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Message Details</h2>
                <button
                  onClick={() => setSelectedMessage(null)}
                  className="text-dark-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* User Info */}
                <div>
                  <label className="text-dark-400 text-sm">Sender</label>
                  <p className="text-white">
                    {selectedMessage.user_first_name} {selectedMessage.user_last_name}
                    {selectedMessage.user_username && ` (@${selectedMessage.user_username})`}
                  </p>
                </div>

                {/* Content */}
                {selectedMessage.content && (
                  <div>
                    <label className="text-dark-400 text-sm">Content</label>
                    <div className="bg-dark-900 rounded p-3 mt-1 border border-dark-700">
                      <p className="text-gray-300 whitespace-pre-wrap break-words">
                        {selectedMessage.content}
                      </p>
                    </div>
                  </div>
                )}

                {/* Deletion Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-dark-400 text-sm">Deletion Reason</label>
                    <p className={`inline-block px-2 py-1 rounded mt-1 ${getReasonBadgeColor(selectedMessage.deletion_reason)}`}>
                      {selectedMessage.deletion_reason.replace('_', ' ')}
                    </p>
                  </div>
                  <div>
                    <label className="text-dark-400 text-sm">Deleted At</label>
                    <p className="text-white">{formatDate(selectedMessage.deleted_at)}</p>
                  </div>
                </div>

                {/* Additional Context */}
                {selectedMessage.trigger_word && (
                  <div>
                    <label className="text-dark-400 text-sm">Trigger Word</label>
                    <p className="text-red-400">{selectedMessage.trigger_word}</p>
                  </div>
                )}

                {selectedMessage.lock_type && (
                  <div>
                    <label className="text-dark-400 text-sm">Lock Type</label>
                    <p className="text-orange-400">{selectedMessage.lock_type}</p>
                  </div>
                )}

                {selectedMessage.ai_confidence !== null && (
                  <div>
                    <label className="text-dark-400 text-sm">AI Confidence</label>
                    <p className="text-blue-400">{(selectedMessage.ai_confidence * 100).toFixed(1)}%</p>
                  </div>
                )}

                {/* Restoration Status */}
                {selectedMessage.restored_at && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded p-3">
                    <p className="text-green-400 flex items-center gap-2">
                      <Check className="w-4 h-4" />
                      Message restored on {formatDate(selectedMessage.restored_at)}
                    </p>
                  </div>
                )}

                {/* Actions */}
                {selectedMessage.can_restore && !selectedMessage.restored_at && (
                  <div className="flex gap-2 pt-4 border-t border-dark-700">
                    <button
                      onClick={() => {
                        handleRestore(selectedMessage.id)
                        setSelectedMessage(null)
                      }}
                      disabled={restoring === selectedMessage.id}
                      className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Restore Message
                    </button>
                    <button
                      onClick={() => {
                        handlePurge(selectedMessage.id)
                        setSelectedMessage(null)
                      }}
                      className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg flex items-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Purge
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
