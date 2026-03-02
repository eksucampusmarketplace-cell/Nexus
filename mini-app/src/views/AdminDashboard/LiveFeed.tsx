import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Radio,
  AlertTriangle,
  Shield,
  Wifi,
  WifiOff,
  Trash2,
  VolumeX,
  Ban,
  UserX,
  ChevronDown,
  Activity,
  MessageSquare,
  Flag,
} from 'lucide-react'
import { useFeedStore } from '../../stores/feedStore'
import type { FeedEvent } from '../../stores/feedStore'
import MemberActionCard from '../../components/Moderation/MemberActionCard'
import type { MemberActionTarget } from '../../components/Moderation/MemberActionCard'

const TRUST_COLOR = (score: number) => {
  if (score >= 70) return 'text-green-400'
  if (score >= 40) return 'text-yellow-400'
  return 'text-red-400'
}

const ROLE_BADGE = (role: string) => {
  switch (role) {
    case 'owner': return 'bg-purple-500/20 text-purple-400'
    case 'admin': return 'bg-blue-500/20 text-blue-400'
    case 'mod': return 'bg-green-500/20 text-green-400'
    case 'trusted': return 'bg-yellow-500/20 text-yellow-400'
    case 'restricted': return 'bg-red-500/20 text-red-400'
    default: return 'bg-dark-700 text-dark-400'
  }
}

const STATUS_ICON = {
  connected: <Wifi className="w-4 h-4 text-green-400" />,
  connecting: <Activity className="w-4 h-4 text-yellow-400 animate-pulse" />,
  disconnected: <WifiOff className="w-4 h-4 text-dark-400" />,
  error: <WifiOff className="w-4 h-4 text-red-400" />,
}

const STATUS_TEXT = {
  connected: 'Live',
  connecting: 'Connecting...',
  disconnected: 'Disconnected',
  error: 'Error',
}

const MOD_ACTION_LABELS: Record<string, { label: string; color: string }> = {
  warn: { label: 'Warned', color: 'text-yellow-400' },
  mute: { label: 'Muted', color: 'text-orange-400' },
  unmute: { label: 'Unmuted', color: 'text-green-400' },
  ban: { label: 'Banned', color: 'text-red-400' },
  unban: { label: 'Unbanned', color: 'text-green-400' },
  kick: { label: 'Kicked', color: 'text-red-400' },
}

interface MessageContextMenu {
  event: FeedEvent
  x: number
  y: number
}

export default function LiveFeed() {
  const { groupId } = useParams<{ groupId: string }>()
  const { events, status, connect, disconnect, sendAction, clearEvents } = useFeedStore()
  const [contextMenu, setContextMenu] = useState<MessageContextMenu | null>(null)
  const [actionTarget, setActionTarget] = useState<MemberActionTarget | null>(null)
  const feedRef = useRef<HTMLDivElement>(null)
  const contextMenuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!groupId) return
    const token = localStorage.getItem('nexus_token')
    if (!token) return

    connect(parseInt(groupId), token)
    return () => {
      disconnect()
    }
  }, [groupId, connect, disconnect])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
        setContextMenu(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleMessageTap = (e: React.MouseEvent, event: FeedEvent) => {
    if (!event.sender) return
    e.preventDefault()
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setContextMenu({
      event,
      x: Math.min(e.clientX, window.innerWidth - 200),
      y: Math.min(rect.bottom + 4, window.innerHeight - 200),
    })
  }

  const openActionCard = (event: FeedEvent) => {
    if (!event.sender || !groupId) return
    setContextMenu(null)
    setActionTarget({
      userId: event.sender.id,
      groupId: parseInt(groupId),
      firstName: event.sender.first_name,
      username: event.sender.username,
      trustScore: event.sender.trust_score,
      level: event.sender.level,
      role: event.sender.role,
      warnCount: 0,
      isMuted: event.sender.is_muted,
      isBanned: false,
    })
  }

  const handleQuickAction = (action: string, event: FeedEvent) => {
    if (!event.sender) return
    setContextMenu(null)
    sendAction(action, event.sender.id)
  }

  const messageEvents = events.filter((e) => e.type === 'message' || e.type === 'mod_action')

  return (
    <div className="py-6 animate-fade-in h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-primary-400" />
            <h1 className="text-xl font-bold text-white">Live Feed</h1>
            <div className="flex items-center gap-1.5 ml-2">
              {STATUS_ICON[status]}
              <span className={`text-xs font-medium ${
                status === 'connected' ? 'text-green-400' :
                status === 'connecting' ? 'text-yellow-400' :
                status === 'error' ? 'text-red-400' : 'text-dark-400'
              }`}>
                {STATUS_TEXT[status]}
              </span>
              {status === 'connected' && (
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
            </div>
          </div>
          <p className="text-dark-400 text-sm mt-0.5">
            Real-time activity stream for your group
          </p>
        </div>
        <button
          onClick={clearEvents}
          className="p-2 bg-dark-800 hover:bg-dark-700 rounded-lg transition-colors"
          title="Clear feed"
        >
          <Trash2 className="w-4 h-4 text-dark-400" />
        </button>
      </div>

      {/* Connection error banner */}
      {status === 'error' && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2 text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>WebSocket connection error. Retrying automatically...</span>
        </div>
      )}

      {/* Feed */}
      <div
        ref={feedRef}
        className="flex-1 space-y-2 overflow-y-auto"
        style={{ minHeight: 0 }}
      >
        {messageEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 bg-dark-800 rounded-full flex items-center justify-center mb-4">
              <MessageSquare className="w-8 h-8 text-dark-600" />
            </div>
            <p className="text-dark-400 font-medium">
              {status === 'connected' ? 'Waiting for messages...' : 'Connect to see live messages'}
            </p>
            <p className="text-dark-600 text-sm mt-1">Messages from your group will appear here in real time</p>
          </div>
        ) : (
          messageEvents.map((event, idx) => (
            <FeedEventItem
              key={`${event.type}-${event.id ?? idx}-${event.timestamp}`}
              event={event}
              onTap={handleMessageTap}
            />
          ))
        )}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          ref={contextMenuRef}
          className="fixed z-40 bg-dark-800 border border-dark-700 rounded-xl shadow-2xl overflow-hidden w-48"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <button
            onClick={() => openActionCard(contextMenu.event)}
            className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-white text-sm transition-colors"
          >
            <Shield className="w-4 h-4 text-dark-400" />
            View Profile & Actions
          </button>
          <button
            onClick={() => handleQuickAction('warn', contextMenu.event)}
            className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-yellow-400 text-sm transition-colors"
          >
            <AlertTriangle className="w-4 h-4" />
            Warn
          </button>
          <button
            onClick={() => handleQuickAction('mute', contextMenu.event)}
            className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-orange-400 text-sm transition-colors"
          >
            <VolumeX className="w-4 h-4" />
            Mute (1h)
          </button>
          <button
            onClick={() => handleQuickAction('ban', contextMenu.event)}
            className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-red-400 text-sm transition-colors"
          >
            <Ban className="w-4 h-4" />
            Ban
          </button>
          <button
            onClick={() => { setContextMenu(null) }}
            className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-dark-400 text-sm transition-colors border-t border-dark-700"
          >
            <Flag className="w-4 h-4" />
            Dismiss
          </button>
        </div>
      )}

      {/* Member Action Card */}
      <MemberActionCard
        target={actionTarget}
        onClose={() => setActionTarget(null)}
        onActionComplete={(action, userId) => {
          sendAction(action, userId)
        }}
      />
    </div>
  )
}

function FeedEventItem({
  event,
  onTap,
}: {
  event: FeedEvent
  onTap: (e: React.MouseEvent, event: FeedEvent) => void
}) {
  if (event.type === 'mod_action') {
    const meta = MOD_ACTION_LABELS[event.action ?? ''] ?? { label: event.action, color: 'text-dark-400' }
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-dark-500">
        <Shield className="w-3.5 h-3.5 flex-shrink-0" />
        <span className={`font-medium ${meta.color}`}>{meta.label}</span>
        <span>user #{event.target_user_id}</span>
        {event.reason && <span className="text-dark-600">— {event.reason}</span>}
        <span className="ml-auto text-dark-700 text-xs">
          {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
        </span>
      </div>
    )
  }

  if (!event.sender) return null

  return (
    <div
      className="group bg-dark-900 rounded-xl border border-dark-800 hover:border-dark-700 p-3 cursor-pointer transition-all select-none"
      onClick={(e) => onTap(e, event)}
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0 w-9 h-9 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
          {event.sender.first_name.charAt(0).toUpperCase()}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white text-sm">{event.sender.first_name}</span>
            {event.sender.username && (
              <span className="text-dark-500 text-xs">@{event.sender.username}</span>
            )}
            <span className={`text-xs px-1.5 py-0.5 rounded ${ROLE_BADGE(event.sender.role)}`}>
              {event.sender.role}
            </span>
            <span className={`text-xs font-medium ${TRUST_COLOR(event.sender.trust_score)}`}>
              ★ {event.sender.trust_score}
            </span>
            <span className="text-xs text-dark-600">Lv.{event.sender.level}</span>
          </div>
          <p className="mt-1 text-dark-200 text-sm break-words line-clamp-3">{event.text}</p>
          {event.ai_flagged && (
            <div className="mt-1.5 flex items-center gap-1.5">
              <Flag className="w-3.5 h-3.5 text-orange-400" />
              <span className="text-xs text-orange-400">
                AI flagged
                {event.ai_confidence !== null && event.ai_confidence !== undefined
                  ? ` — ${Math.round(event.ai_confidence * 100)}% confidence`
                  : ''}
              </span>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className="flex-shrink-0 text-xs text-dark-600 mt-0.5">
          {event.timestamp ? new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
        </div>
      </div>

      {/* Muted indicator */}
      {event.sender.is_muted && (
        <div className="mt-2 flex items-center gap-1 text-xs text-yellow-500/70">
          <VolumeX className="w-3 h-3" />
          User is currently muted
        </div>
      )}
    </div>
  )
}
