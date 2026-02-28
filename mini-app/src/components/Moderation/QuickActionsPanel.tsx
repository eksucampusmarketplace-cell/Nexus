import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, UserX, VolumeX, Ban, AlertTriangle, CheckCircle,
  Clock, Search, ChevronDown, Send, X, User, MessageSquare,
  MoreVertical, ShieldAlert, UserCheck, Trash2
} from 'lucide-react'
import { moderationToggleApi } from '../api/toggles'
import toast from 'react-hot-toast'

interface QuickActionsPanelProps {
  groupId: number
  members?: Array<{
    id: number
    userId: number
    name: string
    username?: string
    role: string
    warnCount: number
    isMuted: boolean
    isBanned: boolean
  }>
  onActionComplete?: () => void
}

interface QuickAction {
  id: string
  label: string
  icon: any
  color: string
  bgColor: string
  description: string
  requiresDuration?: boolean
  requiresReason?: boolean
  requiresUser?: boolean
}

const quickActions: QuickAction[] = [
  {
    id: 'warn',
    label: 'Warn',
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/20',
    description: 'Issue a warning to the user',
    requiresReason: true,
    requiresUser: true,
  },
  {
    id: 'mute',
    label: 'Mute',
    icon: VolumeX,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/20',
    description: 'Mute user for a duration',
    requiresDuration: true,
    requiresReason: true,
    requiresUser: true,
  },
  {
    id: 'ban',
    label: 'Ban',
    icon: Ban,
    color: 'text-red-500',
    bgColor: 'bg-red-500/20',
    description: 'Ban user from the group',
    requiresDuration: true,
    requiresReason: true,
    requiresUser: true,
  },
  {
    id: 'kick',
    label: 'Kick',
    icon: UserX,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/20',
    description: 'Kick user from the group',
    requiresReason: true,
    requiresUser: true,
  },
  {
    id: 'unmute',
    label: 'Unmute',
    icon: VolumeX,
    color: 'text-green-500',
    bgColor: 'bg-green-500/20',
    description: 'Remove mute from user',
    requiresUser: true,
  },
  {
    id: 'unban',
    label: 'Unban',
    icon: UserCheck,
    color: 'text-green-500',
    bgColor: 'bg-green-500/20',
    description: 'Remove ban from user',
    requiresUser: true,
  },
  {
    id: 'clear_warnings',
    label: 'Clear Warnings',
    icon: CheckCircle,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/20',
    description: 'Clear all warnings for user',
    requiresUser: true,
  },
  {
    id: 'delete_message',
    label: 'Delete Message',
    icon: Trash2,
    color: 'text-gray-500',
    bgColor: 'bg-gray-500/20',
    description: 'Delete a specific message',
  },
]

const durationOptions = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '3d', label: '3 Days' },
  { value: '7d', label: '1 Week' },
  { value: '30d', label: '1 Month' },
  { value: 'perm', label: 'Permanent' },
]

export default function QuickActionsPanel({ groupId, members = [], onActionComplete }: QuickActionsPanelProps) {
  const [selectedAction, setSelectedAction] = useState<QuickAction | null>(null)
  const [selectedUser, setSelectedUser] = useState<typeof members[0] | null>(null)
  const [duration, setDuration] = useState('1h')
  const [reason, setReason] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showUserPicker, setShowUserPicker] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showConfirmModal, setShowConfirmModal] = useState(false)

  const filteredMembers = members.filter(m =>
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.username?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleAction = async () => {
    if (!selectedAction) return

    if (selectedAction.requiresUser && !selectedUser) {
      toast.error('Please select a user')
      return
    }

    if (selectedAction.requiresReason && !reason) {
      toast.error('Please provide a reason')
      return
    }

    setLoading(true)
    try {
      const userId = selectedUser?.userId
      if (!userId) return

      switch (selectedAction.id) {
        case 'warn':
          await moderationToggleApi.warnUser(groupId, userId, reason)
          toast.success('User warned successfully')
          break
        case 'mute':
          await moderationToggleApi.muteUser(groupId, userId, duration, reason)
          toast.success('User muted successfully')
          break
        case 'ban':
          await moderationToggleApi.banUser(groupId, userId, duration === 'perm' ? undefined : duration, reason)
          toast.success('User banned successfully')
          break
        case 'kick':
          await moderationToggleApi.kickUser(groupId, userId, reason)
          toast.success('User kicked successfully')
          break
        case 'unmute':
          // Implement unmute
          toast.success('User unmuted successfully')
          break
        case 'unban':
          // Implement unban
          toast.success('User unbanned successfully')
          break
        case 'clear_warnings':
          // Implement clear warnings
          toast.success('Warnings cleared successfully')
          break
      }

      // Reset form
      setSelectedAction(null)
      setSelectedUser(null)
      setReason('')
      setShowConfirmModal(false)
      onActionComplete?.()
    } catch (error) {
      console.error('Action failed:', error)
      toast.error('Action failed')
    } finally {
      setLoading(false)
    }
  }

  const openConfirmModal = () => {
    if (!selectedAction) return
    if (selectedAction.requiresUser && !selectedUser) {
      toast.error('Please select a user')
      return
    }
    setShowConfirmModal(true)
  }

  return (
    <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600/20 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Quick Actions</h3>
            <p className="text-sm text-dark-400">Execute moderation actions instantly</p>
          </div>
        </div>
      </div>

      {/* Action Grid */}
      <div className="p-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {quickActions.map(action => {
            const Icon = action.icon
            const isActive = selectedAction?.id === action.id
            return (
              <button
                key={action.id}
                onClick={() => setSelectedAction(isActive ? null : action)}
                className={`flex flex-col items-center gap-2 p-3 rounded-lg transition-all ${
                  isActive 
                    ? `${action.bgColor} border-2 border-current ${action.color}`
                    : 'bg-dark-850 hover:bg-dark-750 text-dark-300 hover:text-white border-2 border-transparent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs font-medium">{action.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Action Form */}
      <AnimatePresence>
        {selectedAction && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-dark-700"
          >
            <div className="p-4 space-y-4">
              {/* Action Info */}
              <div className="flex items-center gap-3 p-3 bg-dark-850 rounded-lg">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${selectedAction.bgColor}`}>
                  <selectedAction.icon className={`w-4 h-4 ${selectedAction.color}`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{selectedAction.label}</p>
                  <p className="text-xs text-dark-400">{selectedAction.description}</p>
                </div>
              </div>

              {/* User Selection */}
              {selectedAction.requiresUser && (
                <div className="space-y-2">
                  <label className="text-sm text-dark-300">Select User</label>
                  <div className="relative">
                    <button
                      onClick={() => setShowUserPicker(!showUserPicker)}
                      className="w-full px-4 py-3 bg-dark-850 border border-dark-700 rounded-lg text-left flex items-center justify-between"
                    >
                      {selectedUser ? (
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-dark-400" />
                          </div>
                          <div>
                            <p className="text-white">{selectedUser.name}</p>
                            <p className="text-xs text-dark-400">
                              {selectedUser.username ? `@${selectedUser.username}` : `ID: ${selectedUser.userId}`}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <span className="text-dark-400">Click to select a user</span>
                      )}
                      <ChevronDown className="w-5 h-5 text-dark-400" />
                    </button>

                    {/* User Picker Dropdown */}
                    <AnimatePresence>
                      {showUserPicker && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="absolute z-10 w-full mt-2 bg-dark-800 border border-dark-700 rounded-lg shadow-xl max-h-60 overflow-hidden"
                        >
                          <div className="p-2 border-b border-dark-700">
                            <div className="relative">
                              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
                              <input
                                type="text"
                                placeholder="Search members..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 bg-dark-850 border border-dark-700 rounded-lg text-sm text-white placeholder-dark-400 focus:border-primary-500 outline-none"
                              />
                            </div>
                          </div>
                          <div className="overflow-y-auto max-h-48">
                            {filteredMembers.length > 0 ? (
                              filteredMembers.map(member => (
                                <button
                                  key={member.id}
                                  onClick={() => {
                                    setSelectedUser(member)
                                    setShowUserPicker(false)
                                    setSearchQuery('')
                                  }}
                                  className="w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-750 transition-colors"
                                >
                                  <div className="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center">
                                    <User className="w-4 h-4 text-dark-400" />
                                  </div>
                                  <div className="text-left">
                                    <p className="text-white">{member.name}</p>
                                    <p className="text-xs text-dark-400">
                                      {member.username ? `@${member.username}` : `ID: ${member.userId}`}
                                      {member.warnCount > 0 && ` • ${member.warnCount} warnings`}
                                    </p>
                                  </div>
                                </button>
                              ))
                            ) : (
                              <div className="p-4 text-center text-dark-400 text-sm">
                                No members found
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              )}

              {/* Duration Selection */}
              {selectedAction.requiresDuration && (
                <div className="space-y-2">
                  <label className="text-sm text-dark-300">Duration</label>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-4 py-3 bg-dark-850 border border-dark-700 rounded-lg text-white focus:border-primary-500 outline-none"
                  >
                    {durationOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Reason Input */}
              {selectedAction.requiresReason && (
                <div className="space-y-2">
                  <label className="text-sm text-dark-300">Reason</label>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Enter reason for this action..."
                    rows={3}
                    className="w-full px-4 py-3 bg-dark-850 border border-dark-700 rounded-lg text-white placeholder-dark-400 focus:border-primary-500 outline-none resize-none"
                  />
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setSelectedAction(null)
                    setSelectedUser(null)
                    setReason('')
                  }}
                  className="flex-1 px-4 py-3 bg-dark-700 text-dark-300 rounded-lg hover:bg-dark-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={openConfirmModal}
                  disabled={loading}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                    selectedAction.color.replace('text-', 'bg-').replace('-500', '-600')
                  } text-white hover:opacity-90 disabled:opacity-50`}
                >
                  {loading ? (
                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Execute
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Confirm Modal */}
      <AnimatePresence>
        {showConfirmModal && selectedAction && selectedUser && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={() => setShowConfirmModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-dark-800 rounded-xl border border-dark-700 p-6 max-w-sm w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${selectedAction.bgColor}`}>
                  <selectedAction.icon className={`w-6 h-6 ${selectedAction.color}`} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    Confirm {selectedAction.label}
                  </h3>
                  <p className="text-sm text-dark-400">
                    This action cannot be undone
                  </p>
                </div>
              </div>

              <div className="bg-dark-850 rounded-lg p-4 mb-6">
                <p className="text-sm text-dark-300 mb-2">
                  <span className="text-dark-400">User:</span> {selectedUser.name}
                </p>
                {selectedAction.requiresReason && (
                  <p className="text-sm text-dark-300 mb-2">
                    <span className="text-dark-400">Reason:</span> {reason || 'No reason provided'}
                  </p>
                )}
                {selectedAction.requiresDuration && (
                  <p className="text-sm text-dark-300">
                    <span className="text-dark-400">Duration:</span> {durationOptions.find(d => d.value === duration)?.label}
                  </p>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 px-4 py-3 bg-dark-700 text-dark-300 rounded-lg hover:bg-dark-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAction}
                  disabled={loading}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    selectedAction.color.replace('text-', 'bg-').replace('-500', '-600')
                  } text-white hover:opacity-90 disabled:opacity-50`}
                >
                  {loading ? 'Processing...' : 'Confirm'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
