import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield,
  AlertTriangle,
  Check,
  X,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  User,
  Clock,
  Zap,
} from 'lucide-react'
import { getModerationQueue, resolveModerationAction, warnUser, muteUser, banUser, kickUser } from '../../api/moderation'
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

const SEVERITY_COLORS = {
  low: {
    border: 'border-green-500/40',
    badge: 'bg-green-500/20 text-green-400',
    glow: 'shadow-green-500/10',
  },
  medium: {
    border: 'border-yellow-500/40',
    badge: 'bg-yellow-500/20 text-yellow-400',
    glow: 'shadow-yellow-500/10',
  },
  high: {
    border: 'border-orange-500/40',
    badge: 'bg-orange-500/20 text-orange-400',
    glow: 'shadow-orange-500/10',
  },
  critical: {
    border: 'border-red-500/40',
    badge: 'bg-red-500/20 text-red-400',
    glow: 'shadow-red-500/10',
  },
}

const SWIPE_THRESHOLD = 80

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-red-500' : pct >= 60 ? 'bg-orange-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-dark-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-dark-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

interface SwipeCardProps {
  item: QueueItem
  onApprove: (item: QueueItem) => void
  onDismiss: (item: QueueItem) => void
  isTop: boolean
  stackIndex: number
}

function SwipeCard({ item, onApprove, onDismiss, isTop, stackIndex }: SwipeCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const startX = useRef(0)
  const currentX = useRef(0)
  const isDragging = useRef(false)
  const [dragOffset, setDragOffset] = useState(0)
  const [expanded, setExpanded] = useState(false)
  const colors = SEVERITY_COLORS[item.severity]

  const handlePointerDown = (e: React.PointerEvent) => {
    if (!isTop) return
    isDragging.current = true
    startX.current = e.clientX
    currentX.current = e.clientX
    cardRef.current?.setPointerCapture(e.pointerId)
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current || !isTop) return
    currentX.current = e.clientX
    const offset = currentX.current - startX.current
    setDragOffset(offset)
  }

  const handlePointerUp = () => {
    if (!isDragging.current || !isTop) return
    isDragging.current = false

    if (dragOffset > SWIPE_THRESHOLD) {
      onApprove(item)
    } else if (dragOffset < -SWIPE_THRESHOLD) {
      onDismiss(item)
    }

    setDragOffset(0)
  }

  const rotation = isTop ? (dragOffset / 20).toFixed(1) : '0'
  const opacity = isTop ? Math.max(0.3, 1 - Math.abs(dragOffset) / 300) : 1
  const scale = isTop ? 1 : 1 - stackIndex * 0.04
  const translateY = isTop ? 0 : stackIndex * 8

  const approveVisible = isTop && dragOffset > 20
  const dismissVisible = isTop && dragOffset < -20

  return (
    <div
      ref={cardRef}
      className={`absolute inset-x-0 bg-dark-900 rounded-2xl border ${colors.border} shadow-xl ${colors.glow} overflow-hidden`}
      style={{
        transform: `translateX(${dragOffset}px) rotate(${rotation}deg) scale(${scale}) translateY(${translateY}px)`,
        opacity,
        transition: isDragging.current ? 'none' : 'transform 0.3s ease, opacity 0.3s ease',
        zIndex: 10 - stackIndex,
        touchAction: 'none',
      }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {/* Swipe indicators */}
      {approveVisible && (
        <div className="absolute top-4 left-4 z-10 px-3 py-1.5 bg-green-500/90 rounded-lg border-2 border-green-400 font-bold text-white text-sm rotate-[-12deg]">
          ✓ APPROVE
        </div>
      )}
      {dismissVisible && (
        <div className="absolute top-4 right-4 z-10 px-3 py-1.5 bg-red-500/90 rounded-lg border-2 border-red-400 font-bold text-white text-sm rotate-[12deg]">
          ✗ DISMISS
        </div>
      )}

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <span className={`px-2.5 py-0.5 rounded-lg text-xs font-bold uppercase ${colors.badge}`}>
            {item.severity}
          </span>
          <span className="text-dark-400 text-xs">
            {item.type === 'message' ? 'Message' : item.type === 'user' ? 'User' : 'Raid'}
          </span>
          <span className="ml-auto text-dark-600 text-xs flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date(item.created_at).toLocaleString()}
          </span>
        </div>

        {/* Sender mini-profile */}
        {(item.message?.sender || item.user) && (
          <div className="flex items-center gap-3 mb-4 p-3 bg-dark-800 rounded-xl">
            <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
              {((item.message?.sender?.first_name || item.user?.first_name) ?? '?').charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-white text-sm font-medium">
                {item.message?.sender?.first_name || item.user?.first_name}
              </p>
              {(item.message?.sender?.username || item.user?.username) && (
                <p className="text-dark-400 text-xs">
                  @{item.message?.sender?.username || item.user?.username}
                </p>
              )}
              {item.user?.is_new && (
                <p className="text-orange-400 text-xs">
                  New account ({item.user.account_age_days} days)
                </p>
              )}
            </div>
          </div>
        )}

        {/* Message content */}
        {item.message && (
          <div className="mb-4 p-3 bg-dark-800 rounded-xl border border-dark-700">
            <p className={`text-dark-200 text-sm ${expanded ? '' : 'line-clamp-3'}`}>
              {item.message.text}
            </p>
            {item.message.text.length > 150 && (
              <button
                className="mt-2 flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300"
                onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
              >
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        )}

        {/* AI Reason */}
        <div className="mb-4">
          <p className="text-dark-400 text-xs mb-1">AI Reason</p>
          <p className="text-white text-sm">{item.reason}</p>
        </div>

        {/* AI Confidence */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <p className="text-dark-400 text-xs flex items-center gap-1">
              <Zap className="w-3 h-3" />
              AI Confidence
            </p>
          </div>
          <ConfidenceBar value={item.confidence} />
        </div>

        {/* Suggested action */}
        <div className="mb-2">
          <p className="text-dark-500 text-xs">
            Suggested: <span className="text-primary-400 font-medium">{item.suggested_action}</span>
          </p>
        </div>
      </div>

      {/* Swipe hint */}
      {isTop && (
        <div className="px-5 pb-4 flex items-center justify-between text-xs text-dark-600">
          <span>← Swipe left to dismiss</span>
          <span>Swipe right to approve →</span>
        </div>
      )}
    </div>
  )
}

export default function ModerationQueue() {
  const { groupId } = useParams<{ groupId: string }>()
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [dismissed, setDismissed] = useState(0)
  const [approved, setApproved] = useState(0)

  const loadQueue = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const data = await getModerationQueue(parseInt(groupId))
      setQueue(data.items || [])
    } catch {
      toast.error('Failed to load moderation queue')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQueue()
  }, [groupId])

  const removeTop = () => {
    setQueue((prev) => prev.slice(1))
  }

  const handleApprove = async (item: QueueItem) => {
    if (processing) return
    setProcessing(true)
    try {
      if (!groupId) return

      if (item.suggested_action && item.user) {
        switch (item.suggested_action.toLowerCase()) {
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
      }

      await resolveModerationAction(parseInt(groupId), item.id, 'approve')
      setApproved((n) => n + 1)
      removeTop()
      toast.success('Action approved and executed')
    } catch {
      toast.error('Failed to execute action')
    } finally {
      setProcessing(false)
    }
  }

  const handleDismiss = async (item: QueueItem) => {
    if (processing) return
    setProcessing(true)
    try {
      if (!groupId) return
      await resolveModerationAction(parseInt(groupId), item.id, 'dismiss')
      setDismissed((n) => n + 1)
      removeTop()
      toast.success('Dismissed as false positive')
    } catch {
      toast.error('Failed to dismiss')
    } finally {
      setProcessing(false)
    }
  }

  if (loading) return <Loading />

  const visibleCards = queue.slice(0, 3)

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Moderation Queue</h1>
          <p className="text-dark-400 mt-1">
            {queue.length} item{queue.length !== 1 ? 's' : ''} pending review
          </p>
        </div>
        <button
          onClick={loadQueue}
          className="p-2 bg-dark-800 rounded-lg hover:bg-dark-700 transition-colors"
        >
          <RefreshCw className="w-5 h-5 text-dark-400" />
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-3 text-center">
          <p className="text-lg font-bold text-white">{queue.length}</p>
          <p className="text-xs text-dark-400">Pending</p>
        </div>
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-3 text-center">
          <p className="text-lg font-bold text-green-400">{approved}</p>
          <p className="text-xs text-dark-400">Approved</p>
        </div>
        <div className="bg-dark-900 rounded-xl border border-dark-800 p-3 text-center">
          <p className="text-lg font-bold text-dark-400">{dismissed}</p>
          <p className="text-xs text-dark-400">Dismissed</p>
        </div>
      </div>

      {queue.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-10 h-10 text-green-500" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">All Clear!</h3>
          <p className="text-dark-400">No items in the moderation queue</p>
          <p className="text-dark-600 text-sm mt-1">You reviewed {approved + dismissed} items this session</p>
        </div>
      ) : (
        <>
          {/* Card Stack */}
          <div className="relative" style={{ height: '480px' }}>
            {visibleCards.map((item, idx) => (
              <SwipeCard
                key={item.id}
                item={item}
                onApprove={handleApprove}
                onDismiss={handleDismiss}
                isTop={idx === 0}
                stackIndex={idx}
              />
            ))}
          </div>

          {/* Action buttons */}
          <div className="flex gap-4 mt-6 justify-center">
            <button
              onClick={() => queue[0] && handleDismiss(queue[0])}
              disabled={processing || queue.length === 0}
              className="flex items-center gap-2 px-8 py-3 bg-dark-800 hover:bg-dark-700 rounded-2xl text-dark-300 font-medium transition-colors disabled:opacity-50 border border-dark-700"
            >
              <X className="w-5 h-5 text-red-400" />
              Dismiss
            </button>
            <button
              onClick={() => queue[0] && handleApprove(queue[0])}
              disabled={processing || queue.length === 0}
              className="flex items-center gap-2 px-8 py-3 bg-green-600 hover:bg-green-500 rounded-2xl text-white font-medium transition-colors disabled:opacity-50"
            >
              <Check className="w-5 h-5" />
              Approve
            </button>
          </div>

          <p className="text-center text-dark-600 text-xs mt-3">
            Or swipe the card left / right
          </p>
        </>
      )}
    </div>
  )
}
