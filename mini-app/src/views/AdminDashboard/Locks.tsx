import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Lock,
  Unlock,
  Clock,
  Shield,
  Bot,
  Link,
  Image,
  FileText,
  Volume2,
  MapPin,
  Phone,
  Contact,
  CreditCard,
  Hash,
  MessageCircle,
  Gamepad2,
  Globe,
  Mail,
  AlertTriangle,
  Settings,
} from 'lucide-react'
import { getLocks, updateLock, bulkUpdateLocks } from '../../api/locks'
import Card from '../../components/UI/Card'
import Toggle from '../../components/UI/Toggle'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

interface Lock {
  lock_type: string
  is_locked: boolean
  mode: string
  mode_duration: number | null
  schedule_enabled: boolean
  schedule_windows: { from: string; to: string }[] | null
}

const lockTypeConfig: Record<string, { icon: React.ElementType; label: string; description: string }> = {
  audio: { icon: Volume2, label: 'Audio', description: 'Voice messages and audio files' },
  bot: { icon: Bot, label: 'Bots', description: 'Adding bots to the group' },
  button: { icon: Link, label: 'Inline Buttons', description: 'Messages with inline keyboards' },
  command: { icon: Hash, label: 'Commands', description: 'Commands (slash commands)' },
  contact: { icon: Contact, label: 'Contacts', description: 'Sharing contacts' },
  document: { icon: FileText, label: 'Documents', description: 'Document files' },
  email: { icon: Mail, label: 'Emails', description: 'Email addresses in messages' },
  forward: { icon: MessageCircle, label: 'Forwards', description: 'Forwarded messages' },
  game: { icon: Gamepad2, label: 'Games', description: 'Game messages' },
  location: { icon: MapPin, label: 'Locations', description: 'Location sharing' },
  phone: { icon: Phone, label: 'Phone Numbers', description: 'Phone numbers in messages' },
  photo: { icon: Image, label: 'Photos', description: 'Photo messages' },
  sticker: { icon: Hash, label: 'Stickers', description: 'Sticker messages' },
  url: { icon: Link, label: 'URLs', description: 'Links in messages' },
  video: { icon: Image, label: 'Videos', description: 'Video messages' },
  voice: { icon: Volume2, label: 'Voice', description: 'Voice messages' },
  arabic: { icon: Globe, label: 'Arabic', description: 'Arabic script' },
  rtl: { icon: AlertTriangle, label: 'RTL', description: 'Right-to-left characters' },
  spoiler: { icon: AlertTriangle, label: 'Spoilers', description: 'Spoiler tags' },
}

const modeOptions = [
  { value: 'delete', label: 'Delete', description: 'Just delete the message' },
  { value: 'warn', label: 'Warn', description: 'Delete and warn the user' },
  { value: 'kick', label: 'Kick', description: 'Kick the user from group' },
  { value: 'ban', label: 'Ban', description: 'Ban the user permanently' },
  { value: 'tban', label: 'Temp Ban', description: 'Ban for a specified duration' },
  { value: 'tmute', label: 'Temp Mute', description: 'Mute for a specified duration' },
]

export default function Locks() {
  const { groupId } = useParams<{ groupId: string }>()
  const [locks, setLocks] = useState<Lock[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedLock, setSelectedLock] = useState<Lock | null>(null)
  const [showSchedule, setShowSchedule] = useState(false)

  const loadLocks = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const data = await getLocks(parseInt(groupId))
      setLocks(data.items || data || [])
    } catch (error) {
      toast.error('Failed to load locks')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLocks()
  }, [groupId])

  const handleToggle = async (lockType: string, currentStatus: boolean) => {
    if (!groupId) return
    try {
      await updateLock(parseInt(groupId), lockType, { is_locked: !currentStatus })
      setLocks(locks.map((l) => (l.lock_type === lockType ? { ...l, is_locked: !currentStatus } : l)))
      toast.success(`${lockType} ${!currentStatus ? 'locked' : 'unlocked'}`)
    } catch (error) {
      toast.error('Failed to update lock')
    }
  }

  const handleModeChange = async (lockType: string, mode: string) => {
    if (!groupId) return
    try {
      await updateLock(parseInt(groupId), lockType, { mode })
      setLocks(locks.map((l) => (l.lock_type === lockType ? { ...l, mode } : l)))
      toast.success('Mode updated')
    } catch (error) {
      toast.error('Failed to update mode')
    }
  }

  const lockedCount = locks.filter((l) => l.is_locked).length

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Content Locks</h1>
          <p className="text-dark-400 mt-1">
            {lockedCount} of {locks.length} locks active
          </p>
        </div>
        <button
          onClick={() => {
            const allUnlocked = locks.map((l) => ({ lock_type: l.lock_type, is_locked: true }))
            bulkUpdateLocks(parseInt(groupId!), allUnlocked).then(() => {
              setLocks(locks.map((l) => ({ ...l, is_locked: true })))
              toast.success('All locks enabled')
            })
          }}
          className="px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-dark-300 transition-colors"
        >
          Lock All
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="text-center">
          <Lock className="w-8 h-8 text-green-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">{lockedCount}</div>
          <div className="text-dark-500 text-sm">Active Locks</div>
        </Card>
        <Card className="text-center">
          <Shield className="w-8 h-8 text-blue-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">{locks.length - lockedCount}</div>
          <div className="text-dark-500 text-sm">Unlocked</div>
        </Card>
        <Card className="text-center">
          <Clock className="w-8 h-8 text-purple-400 mx-auto mb-2" />
          <div className="text-2xl font-bold text-white">
            {locks.filter((l) => l.schedule_enabled).length}
          </div>
          <div className="text-dark-500 text-sm">Scheduled</div>
        </Card>
      </div>

      {/* Lock Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {locks.map((lock) => {
          const config = lockTypeConfig[lock.lock_type] || {
            icon: Lock,
            label: lock.lock_type,
            description: '',
          }
          const Icon = config.icon

          return (
            <Card
              key={lock.lock_type}
              className={`cursor-pointer transition-all ${
                lock.is_locked ? 'border-green-500/30 bg-green-500/5' : 'hover:border-dark-700'
              }`}
              onClick={() => setSelectedLock(lock)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${lock.is_locked ? 'bg-green-500/20' : 'bg-dark-800'}`}>
                  <Icon className={`w-5 h-5 ${lock.is_locked ? 'text-green-400' : 'text-dark-400'}`} />
                </div>
                <Toggle
                  checked={lock.is_locked}
                  onChange={() => handleToggle(lock.lock_type, lock.is_locked)}
                />
              </div>
              <h3 className="font-semibold text-white mb-1">{config.label}</h3>
              <p className="text-dark-500 text-xs line-clamp-2">{config.description}</p>
              {lock.is_locked && lock.mode !== 'delete' && (
                <div className="mt-3 pt-3 border-t border-dark-800">
                  <span className="text-xs text-dark-400">
                    Mode: <span className="text-primary-400 capitalize">{lock.mode}</span>
                  </span>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      {/* Lock Detail Modal */}
      {selectedLock && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">
                {lockTypeConfig[selectedLock.lock_type]?.label || selectedLock.lock_type}
              </h2>
              <button
                onClick={() => setSelectedLock(null)}
                className="text-dark-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-white">Status</h3>
                  <p className="text-dark-500 text-sm">
                    {selectedLock.is_locked ? 'Content is blocked' : 'Content is allowed'}
                  </p>
                </div>
                <Toggle
                  checked={selectedLock.is_locked}
                  onChange={() => {
                    handleToggle(selectedLock.lock_type, selectedLock.is_locked)
                    setSelectedLock({ ...selectedLock, is_locked: !selectedLock.is_locked })
                  }}
                />
              </div>

              {/* Mode Selection */}
              <div>
                <h3 className="font-medium text-white mb-3">Action Mode</h3>
                <div className="space-y-2">
                  {modeOptions.map((mode) => (
                    <button
                      key={mode.value}
                      onClick={() => {
                        handleModeChange(selectedLock.lock_type, mode.value)
                        setSelectedLock({ ...selectedLock, mode: mode.value })
                      }}
                      className={`w-full p-3 rounded-xl text-left transition-colors ${
                        selectedLock.mode === mode.value
                          ? 'bg-primary-600/20 border border-primary-500'
                          : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                      }`}
                    >
                      <div className="font-medium text-white">{mode.label}</div>
                      <div className="text-dark-500 text-sm">{mode.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Schedule */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-white">Schedule</h3>
                  <button
                    onClick={() => setShowSchedule(!showSchedule)}
                    className="text-primary-400 text-sm"
                  >
                    {showSchedule ? 'Hide' : 'Configure'}
                  </button>
                </div>
                {showSchedule && (
                  <div className="p-4 bg-dark-800 rounded-xl">
                    <p className="text-dark-400 text-sm">
                      Configure time windows when this lock should be active
                    </p>
                    <button className="mt-3 w-full py-2 bg-dark-700 hover:bg-dark-600 rounded-lg text-dark-300 text-sm">
                      Add Time Window
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
