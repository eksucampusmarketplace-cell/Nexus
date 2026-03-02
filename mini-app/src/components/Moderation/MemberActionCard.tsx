import { useState, useEffect, useRef } from 'react'
import {
  X,
  AlertTriangle,
  VolumeX,
  Ban,
  UserX,
  Shield,
  MessageSquare,
  Star,
  Clock,
  ChevronDown,
} from 'lucide-react'
import { warnMember, muteMember, banMember, kickMember, unmuteMember, unbanMember } from '../../api/members'
import toast from 'react-hot-toast'

export interface MemberActionTarget {
  userId: number
  groupId: number
  firstName: string
  username: string | null
  trustScore: number
  level: number
  role: string
  warnCount: number
  isMuted: boolean
  isBanned: boolean
  joinedAt?: string
}

interface MemberActionCardProps {
  target: MemberActionTarget | null
  onClose: () => void
  onActionComplete?: (action: string, userId: number) => void
}

const DURATION_OPTIONS = [
  { label: '30 min', value: '30m' },
  { label: '1 hour', value: '1h' },
  { label: '2 hours', value: '2h' },
  { label: '6 hours', value: '6h' },
  { label: '12 hours', value: '12h' },
  { label: '1 day', value: '1d' },
  { label: '3 days', value: '3d' },
  { label: '7 days', value: '7d' },
  { label: 'Permanent', value: '' },
]

const TRUST_COLOR = (score: number) => {
  if (score >= 70) return 'text-green-400'
  if (score >= 40) return 'text-yellow-400'
  return 'text-red-400'
}

const ROLE_COLOR = (role: string) => {
  switch (role) {
    case 'owner': return 'text-purple-400'
    case 'admin': return 'text-blue-400'
    case 'mod': return 'text-green-400'
    case 'trusted': return 'text-yellow-400'
    case 'restricted': return 'text-red-400'
    default: return 'text-dark-400'
  }
}

export default function MemberActionCard({ target, onClose, onActionComplete }: MemberActionCardProps) {
  const [loading, setLoading] = useState<string | null>(null)
  const [showMutePicker, setShowMutePicker] = useState(false)
  const [showBanPicker, setShowBanPicker] = useState(false)
  const [reason, setReason] = useState('')
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    if (target) {
      setReason('')
      setShowMutePicker(false)
      setShowBanPicker(false)
    }
  }, [target])

  if (!target) return null

  const handleWarn = async () => {
    setLoading('warn')
    try {
      await warnMember(target.groupId, target.userId, { reason: reason || undefined })
      toast.success(`${target.firstName} warned`)
      onActionComplete?.('warn', target.userId)
      onClose()
    } catch {
      toast.error('Failed to warn user')
    } finally {
      setLoading(null)
    }
  }

  const handleMute = async (duration: string) => {
    setLoading('mute')
    try {
      await muteMember(target.groupId, target.userId, { duration: duration || undefined, reason: reason || undefined })
      toast.success(`${target.firstName} muted${duration ? ` for ${DURATION_OPTIONS.find(d => d.value === duration)?.label}` : ' permanently'}`)
      onActionComplete?.('mute', target.userId)
      onClose()
    } catch {
      toast.error('Failed to mute user')
    } finally {
      setLoading(null)
      setShowMutePicker(false)
    }
  }

  const handleUnmute = async () => {
    setLoading('unmute')
    try {
      await unmuteMember(target.groupId, target.userId)
      toast.success(`${target.firstName} unmuted`)
      onActionComplete?.('unmute', target.userId)
      onClose()
    } catch {
      toast.error('Failed to unmute user')
    } finally {
      setLoading(null)
    }
  }

  const handleBan = async (duration: string) => {
    setLoading('ban')
    try {
      await banMember(target.groupId, target.userId, { duration: duration || undefined, reason: reason || undefined })
      toast.success(`${target.firstName} banned${duration ? ` for ${DURATION_OPTIONS.find(d => d.value === duration)?.label}` : ' permanently'}`)
      onActionComplete?.('ban', target.userId)
      onClose()
    } catch {
      toast.error('Failed to ban user')
    } finally {
      setLoading(null)
      setShowBanPicker(false)
    }
  }

  const handleUnban = async () => {
    setLoading('unban')
    try {
      await unbanMember(target.groupId, target.userId)
      toast.success(`${target.firstName} unbanned`)
      onActionComplete?.('unban', target.userId)
      onClose()
    } catch {
      toast.error('Failed to unban user')
    } finally {
      setLoading(null)
    }
  }

  const handleKick = async () => {
    setLoading('kick')
    try {
      await kickMember(target.groupId, target.userId, reason || undefined)
      toast.success(`${target.firstName} kicked`)
      onActionComplete?.('kick', target.userId)
      onClose()
    } catch {
      toast.error('Failed to kick user')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose()
      }}
      ref={overlayRef}
    >
      <div
        className="w-full sm:max-w-md bg-dark-900 rounded-t-2xl sm:rounded-2xl border border-dark-700 shadow-2xl animate-fade-in overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-800">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-lg font-bold text-white">
              {target.firstName.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-white">{target.firstName}</h3>
                {target.isMuted && (
                  <span className="text-xs px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded">Muted</span>
                )}
                {target.isBanned && (
                  <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">Banned</span>
                )}
              </div>
              {target.username && (
                <p className="text-sm text-dark-400">@{target.username}</p>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-dark-800 rounded-lg transition-colors">
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 p-4 border-b border-dark-800">
          <div className="text-center">
            <p className={`text-lg font-bold ${TRUST_COLOR(target.trustScore)}`}>{target.trustScore}</p>
            <p className="text-xs text-dark-500">Trust</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-white">{target.level}</p>
            <p className="text-xs text-dark-500">Level</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-orange-400">{target.warnCount}</p>
            <p className="text-xs text-dark-500">Warns</p>
          </div>
          <div className="text-center">
            <p className={`text-sm font-bold ${ROLE_COLOR(target.role)}`}>{target.role}</p>
            <p className="text-xs text-dark-500">Role</p>
          </div>
        </div>

        {/* Reason input */}
        <div className="px-4 pt-3">
          <input
            type="text"
            placeholder="Reason (optional)..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>

        {/* Actions */}
        <div className="p-4 space-y-2">
          {/* Warn */}
          <button
            onClick={handleWarn}
            disabled={!!loading}
            className="w-full flex items-center gap-3 px-4 py-3 bg-yellow-500/10 hover:bg-yellow-500/20 border border-yellow-500/20 rounded-xl text-yellow-400 transition-colors disabled:opacity-50"
          >
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Warn</span>
            {loading === 'warn' && <span className="ml-auto text-xs">...</span>}
          </button>

          {/* Mute / Unmute */}
          {target.isMuted ? (
            <button
              onClick={handleUnmute}
              disabled={!!loading}
              className="w-full flex items-center gap-3 px-4 py-3 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 rounded-xl text-green-400 transition-colors disabled:opacity-50"
            >
              <VolumeX className="w-5 h-5" />
              <span className="font-medium">Unmute</span>
              {loading === 'unmute' && <span className="ml-auto text-xs">...</span>}
            </button>
          ) : (
            <div>
              <button
                onClick={() => { setShowMutePicker(!showMutePicker); setShowBanPicker(false) }}
                disabled={!!loading}
                className="w-full flex items-center gap-3 px-4 py-3 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 rounded-xl text-orange-400 transition-colors disabled:opacity-50"
              >
                <VolumeX className="w-5 h-5" />
                <span className="font-medium">Mute</span>
                <ChevronDown className={`ml-auto w-4 h-4 transition-transform ${showMutePicker ? 'rotate-180' : ''}`} />
              </button>
              {showMutePicker && (
                <div className="mt-1 bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
                  {DURATION_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleMute(opt.value)}
                      disabled={!!loading}
                      className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-dark-300 text-sm transition-colors disabled:opacity-50"
                    >
                      <Clock className="w-4 h-4 text-dark-500" />
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Ban / Unban */}
          {target.isBanned ? (
            <button
              onClick={handleUnban}
              disabled={!!loading}
              className="w-full flex items-center gap-3 px-4 py-3 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 rounded-xl text-green-400 transition-colors disabled:opacity-50"
            >
              <Shield className="w-5 h-5" />
              <span className="font-medium">Unban</span>
              {loading === 'unban' && <span className="ml-auto text-xs">...</span>}
            </button>
          ) : (
            <div>
              <button
                onClick={() => { setShowBanPicker(!showBanPicker); setShowMutePicker(false) }}
                disabled={!!loading}
                className="w-full flex items-center gap-3 px-4 py-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl text-red-400 transition-colors disabled:opacity-50"
              >
                <Ban className="w-5 h-5" />
                <span className="font-medium">Ban</span>
                <ChevronDown className={`ml-auto w-4 h-4 transition-transform ${showBanPicker ? 'rotate-180' : ''}`} />
              </button>
              {showBanPicker && (
                <div className="mt-1 bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
                  {DURATION_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => handleBan(opt.value)}
                      disabled={!!loading}
                      className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-dark-700 text-dark-300 text-sm transition-colors disabled:opacity-50"
                    >
                      <Clock className="w-4 h-4 text-dark-500" />
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Kick */}
          <button
            onClick={handleKick}
            disabled={!!loading}
            className="w-full flex items-center gap-3 px-4 py-3 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl text-red-400 transition-colors disabled:opacity-50"
          >
            <UserX className="w-5 h-5" />
            <span className="font-medium">Kick</span>
            {loading === 'kick' && <span className="ml-auto text-xs">...</span>}
          </button>
        </div>
      </div>
    </div>
  )
}
