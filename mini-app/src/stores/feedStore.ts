import { create } from 'zustand'

export type FeedEventType = 'message' | 'mod_action' | 'member_join' | 'member_leave' | 'ping' | 'pong' | 'action_result' | 'error'

export interface FeedSender {
  id: number
  first_name: string
  username: string | null
  trust_score: number
  level: number
  role: string
  is_muted: boolean
}

export interface FeedEvent {
  type: FeedEventType
  id?: number
  text?: string
  sender?: FeedSender
  timestamp?: string
  ai_flagged?: boolean
  ai_confidence?: number | null
  action?: string
  target_user_id?: number
  actor_id?: number
  reason?: string
  message?: string
  success?: boolean
  user_id?: number
}

type WsStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface FeedState {
  events: FeedEvent[]
  status: WsStatus
  error: string | null
  ws: WebSocket | null
  groupId: number | null

  connect: (groupId: number, token: string) => void
  disconnect: () => void
  sendAction: (action: string, userId: number, options?: { reason?: string; duration?: string }) => void
  clearEvents: () => void
  _addEvent: (event: FeedEvent) => void
  _setStatus: (status: WsStatus) => void
  _setError: (error: string | null) => void
}

const MAX_EVENTS = 200

function getWsBaseUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL as string | undefined
  if (apiUrl) {
    return apiUrl.replace(/^http/, 'ws')
  }
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }
  return 'wss://nexus-4uxn.onrender.com'
}

export const useFeedStore = create<FeedState>((set, get) => ({
  events: [],
  status: 'disconnected',
  error: null,
  ws: null,
  groupId: null,

  connect: (groupId, token) => {
    const { ws: existing, groupId: currentGroup } = get()

    if (existing && currentGroup === groupId && existing.readyState <= WebSocket.OPEN) {
      return
    }

    if (existing) {
      existing.close()
    }

    set({ status: 'connecting', error: null, groupId })

    const base = getWsBaseUrl()
    const url = `${base}/api/v1/ws/groups/${groupId}/feed?token=${encodeURIComponent(token)}`

    let ws: WebSocket
    try {
      ws = new WebSocket(url)
    } catch (e) {
      set({ status: 'error', error: 'Failed to create WebSocket connection', ws: null })
      return
    }

    ws.onopen = () => {
      set({ status: 'connected', error: null })
    }

    ws.onmessage = (event) => {
      try {
        const data: FeedEvent = JSON.parse(event.data)
        if (data.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }))
          return
        }
        get()._addEvent(data)
      } catch {
        // malformed message
      }
    }

    ws.onerror = () => {
      set({ status: 'error', error: 'WebSocket connection error' })
    }

    ws.onclose = (e) => {
      const { status } = get()
      if (status !== 'disconnected') {
        set({ status: 'disconnected', ws: null })
        if (e.code !== 1000 && e.code !== 4001 && e.code !== 4003) {
          setTimeout(() => {
            const { groupId: gid, status: s } = get()
            if (gid && s === 'disconnected') {
              get().connect(groupId, token)
            }
          }, 3000)
        }
      }
    }

    set({ ws })
  },

  disconnect: () => {
    const { ws } = get()
    if (ws) {
      ws.close(1000)
    }
    set({ status: 'disconnected', ws: null, groupId: null })
  },

  sendAction: (action, userId, options = {}) => {
    const { ws, status } = get()
    if (!ws || status !== 'connected') return
    ws.send(JSON.stringify({
      type: 'action',
      action,
      user_id: userId,
      reason: options.reason,
      duration: options.duration,
    }))
  },

  clearEvents: () => set({ events: [] }),

  _addEvent: (event) => {
    set((state) => ({
      events: [event, ...state.events].slice(0, MAX_EVENTS),
    }))
  },

  _setStatus: (status) => set({ status }),
  _setError: (error) => set({ error }),
}))
