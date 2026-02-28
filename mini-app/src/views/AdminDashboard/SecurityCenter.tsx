import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield,
  Lock,
  Eye,
  Trash2,
  AlertTriangle,
  Users,
  MessageSquare,
  Link2,
  Image,
  File,
  Sticker,
  Gamepad2,
  Bot,
  Settings,
  ToggleLeft,
  ToggleRight,
  Save,
  RefreshCw,
  Ban,
  Warning,
  Filter,
  Globe,
  Hash,
  Bell,
  BellOff,
} from 'lucide-react'
import api from '../api/client'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

interface LockSettings {
  lock_links: boolean
  lock_stickers: boolean
  lock_gifs: boolean
  lock_photos: boolean
  lock_videos: boolean
  lock_documents: boolean
  lock_audio: boolean
  lock_voice: boolean
  lock_forwards: boolean
  lock_games: boolean
  lock_bot_commands: boolean
  lock_inline: boolean
}

interface AntiSpamSettings {
  enabled: boolean
  max_messages_per_minute: number
  max_duplicates: number
  max_links_per_message: number
  warn_threshold: number
  mute_threshold: number
  ban_threshold: number
}

interface BlocklistSettings {
  enabled: boolean
  strict_mode: boolean
  auto_delete: boolean
  warn_user: boolean
}

interface FilterSettings {
  enabled: boolean
  delete_violations: boolean
}

interface CaptchaSettings {
  enabled: boolean
  type: 'button' | 'math' | 'button_math'
  difficulty: 'easy' | 'medium' | 'hard'
  timeout: number
}

export default function SecurityCenter() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'locks' | 'antispam' | 'blocklist' | 'captcha'>('locks')
  const [saving, setSaving] = useState(false)
  
  // Settings states
  const [locks, setLocks] = useState<LockSettings>({
    lock_links: false,
    lock_stickers: false,
    lock_gifs: false,
    lock_photos: false,
    lock_videos: false,
    lock_documents: false,
    lock_audio: false,
    lock_voice: false,
    lock_forwards: false,
    lock_games: false,
    lock_bot_commands: false,
    lock_inline: false,
  })
  
  const [antispam, setAntispam] = useState<AntiSpamSettings>({
    enabled: true,
    max_messages_per_minute: 5,
    max_duplicates: 3,
    max_links_per_message: 2,
    warn_threshold: 3,
    mute_threshold: 5,
    ban_threshold: 8,
  })
  
  const [blocklist, setBlocklist] = useState<BlocklistSettings>({
    enabled: true,
    strict_mode: false,
    auto_delete: true,
    warn_user: true,
  })
  
  const [captcha, setCaptcha] = useState<CaptchaSettings>({
    enabled: false,
    type: 'button',
    difficulty: 'medium',
    timeout: 300,
  })

  const loadSettings = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      // Load locks config
      try {
        const locksRes = await api.get(`/groups/${groupId}/modules/locks/config`)
        if (locksRes.data?.config) {
          setLocks(prev => ({ ...prev, ...locksRes.data.config }))
        }
      } catch (e) { /* ignore */ }

      // Load antispam config
      try {
        const spamRes = await api.get(`/groups/${groupId}/modules/antispam/config`)
        if (spamRes.data?.config) {
          setAntispam(prev => ({ ...prev, ...spamRes.data.config }))
        }
      } catch (e) { /* ignore */ }

      // Load captcha config
      try {
        const captchaRes = await api.get(`/groups/${groupId}/modules/captcha/config`)
        if (captchaRes.data?.config) {
          setCaptcha(prev => ({ ...prev, ...captchaRes.data.config }))
        }
      } catch (e) { /* ignore */ }
    } catch (error) {
      console.error('Failed to load security settings:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [groupId])

  const handleSave = async () => {
    if (!groupId) return
    setSaving(true)
    try {
      // Save locks
      await api.patch(`/groups/${groupId}/modules/locks/config`, {
        config: locks,
        is_enabled: true,
      })
      
      // Save antispam
      await api.patch(`/groups/${groupId}/modules/antispam/config`, {
        config: antispam,
        is_enabled: antispam.enabled,
      })

      // Save captcha
      await api.patch(`/groups/${groupId}/modules/captcha/config`, {
        config: captcha,
        is_enabled: captcha.enabled,
      })

      toast.success('Security settings saved!')
    } catch (error) {
      console.error('Failed to save settings:', error)
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const toggleLock = (key: keyof LockSettings) => {
    setLocks(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const lockItems = [
    { key: 'lock_links', label: 'Links', icon: Link2, description: 'Block messages with URLs' },
    { key: 'lock_stickers', label: 'Stickers', icon: File, description: 'Block sticker messages' },
    { key: 'lock_gifs', label: 'GIFs', icon: Image, description: 'Block animated stickers' },
    { key: 'lock_photos', label: 'Photos', icon: Image, description: 'Block image messages' },
    { key: 'lock_videos', label: 'Videos', icon: File, description: 'Block video messages' },
    { key: 'lock_documents', label: 'Documents', icon: File, description: 'Block file attachments' },
    { key: 'lock_audio', label: 'Audio', icon: File, description: 'Block audio files' },
    { key: 'lock_voice', label: 'Voice', icon: File, description: 'Block voice messages' },
    { key: 'lock_forwards', label: 'Forwards', icon: RefreshCw, description: 'Block forwarded messages' },
    { key: 'lock_games', label: 'Games', icon: Gamepad2, description: 'Block game invites' },
    { key: 'lock_bot_commands', label: 'Bot Commands', icon: Bot, description: 'Block /command usage' },
    { key: 'lock_inline', label: 'Inline Queries', icon: Hash, description: 'Block inline bots' },
  ]

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center">
            <Shield className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Security Center</h1>
            <p className="text-dark-400 mt-1">Manage all security settings in one place</p>
          </div>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {[
          { id: 'locks', label: 'Content Locks', icon: Lock },
          { id: 'antispam', label: 'Anti-Spam', icon: AlertTriangle },
          { id: 'blocklist', label: 'Blocklist', icon: Ban },
          { id: 'captcha', label: 'Verification', icon: Shield },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Locks Tab */}
      {activeTab === 'locks' && (
        <Card title="Content Locks" icon={Lock} description="Control what users can send in your group">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
            {lockItems.map(item => (
              <button
                key={item.key}
                onClick={() => toggleLock(item.key as keyof LockSettings)}
                className={`p-4 rounded-xl border transition-all text-left ${
                  locks[item.key as keyof LockSettings]
                    ? 'bg-red-500/10 border-red-500/30'
                    : 'bg-dark-800/50 border-dark-700 hover:border-dark-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <item.icon className={`w-5 h-5 ${locks[item.key as keyof LockSettings] ? 'text-red-400' : 'text-dark-400'}`} />
                  {locks[item.key as keyof LockSettings] ? (
                    <Lock className="w-4 h-4 text-red-400" />
                  ) : (
                    <Lock className="w-4 h-4 text-dark-600" />
                  )}
                </div>
                <p className={`font-medium ${locks[item.key as keyof LockSettings] ? 'text-red-400' : 'text-white'}`}>
                  {item.label}
                </p>
                <p className="text-dark-500 text-xs mt-1">{item.description}</p>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Anti-Spam Tab */}
      {activeTab === 'antispam' && (
        <div className="space-y-6">
          <Card title="Anti-Spam Protection" icon={AlertTriangle}>
            <div className="space-y-4 mt-4">
              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Enable Anti-Spam</p>
                  <p className="text-dark-400 text-sm">Automatically detect and block spam</p>
                </div>
                <button
                  onClick={() => setAntispam(prev => ({ ...prev, enabled: !prev.enabled }))}
                  className={`p-2 rounded-lg transition-colors ${
                    antispam.enabled ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {antispam.enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Max Messages/Min</label>
                  <input
                    type="number"
                    value={antispam.max_messages_per_minute}
                    onChange={(e) => setAntispam(prev => ({ ...prev, max_messages_per_minute: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Max Duplicates</label>
                  <input
                    type="number"
                    value={antispam.max_duplicates}
                    onChange={(e) => setAntispam(prev => ({ ...prev, max_duplicates: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Max Links/Message</label>
                  <input
                    type="number"
                    value={antispam.max_links_per_message}
                    onChange={(e) => setAntispam(prev => ({ ...prev, max_links_per_message: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Warn Threshold</label>
                  <input
                    type="number"
                    value={antispam.warn_threshold}
                    onChange={(e) => setAntispam(prev => ({ ...prev, warn_threshold: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
              </div>
            </div>
          </Card>

          <Card title="Action Thresholds" icon={Warning}>
            <div className="space-y-4 mt-4">
              <div className="p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white">Warn after</span>
                  <span className="text-primary-400 font-medium">{antispam.warn_threshold} violations</span>
                </div>
                <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-yellow-500 rounded-full"
                    style={{ width: `${(antispam.warn_threshold / 10) * 100}%` }}
                  />
                </div>
              </div>
              <div className="p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white">Mute after</span>
                  <span className="text-orange-400 font-medium">{antispam.mute_threshold} violations</span>
                </div>
                <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${(antispam.mute_threshold / 10) * 100}%` }}
                  />
                </div>
              </div>
              <div className="p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white">Ban after</span>
                  <span className="text-red-400 font-medium">{antispam.ban_threshold} violations</span>
                </div>
                <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${(antispam.ban_threshold / 10) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Blocklist Tab */}
      {activeTab === 'blocklist' && (
        <div className="space-y-6">
          <Card title="Blocklist Settings" icon={Ban}>
            <div className="space-y-4 mt-4">
              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Enable Blocklist</p>
                  <p className="text-dark-400 text-sm">Block specific words and phrases</p>
                </div>
                <button
                  onClick={() => setBlocklist(prev => ({ ...prev, enabled: !prev.enabled }))}
                  className={`p-2 rounded-lg transition-colors ${
                    blocklist.enabled ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {blocklist.enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Strict Mode</p>
                  <p className="text-dark-400 text-sm">Match words with any characters in between</p>
                </div>
                <button
                  onClick={() => setBlocklist(prev => ({ ...prev, strict_mode: !prev.strict_mode }))}
                  className={`p-2 rounded-lg transition-colors ${
                    blocklist.strict_mode ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {blocklist.strict_mode ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Auto-Delete</p>
                  <p className="text-dark-400 text-sm">Automatically delete messages with blocked words</p>
                </div>
                <button
                  onClick={() => setBlocklist(prev => ({ ...prev, auto_delete: !prev.auto_delete }))}
                  className={`p-2 rounded-lg transition-colors ${
                    blocklist.auto_delete ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {blocklist.auto_delete ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Warn User</p>
                  <p className="text-dark-400 text-sm">Warn user when they use blocked words</p>
                </div>
                <button
                  onClick={() => setBlocklist(prev => ({ ...prev, warn_user: !prev.warn_user }))}
                  className={`p-2 rounded-lg transition-colors ${
                    blocklist.warn_user ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {blocklist.warn_user ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Captcha Tab */}
      {activeTab === 'captcha' && (
        <div className="space-y-6">
          <Card title="Verification (Captcha)" icon={Shield}>
            <div className="space-y-4 mt-4">
              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Enable Verification</p>
                  <p className="text-dark-400 text-sm">Require new members to verify</p>
                </div>
                <button
                  onClick={() => setCaptcha(prev => ({ ...prev, enabled: !prev.enabled }))}
                  className={`p-2 rounded-lg transition-colors ${
                    captcha.enabled ? 'bg-green-500/20 text-green-400' : 'bg-dark-700 text-dark-400'
                  }`}
                >
                  {captcha.enabled ? <ToggleRight className="w-8 h-8" /> : <ToggleLeft className="w-8 h-8" />}
                </button>
              </div>

              {captcha.enabled && (
                <>
                  <div className="p-4 bg-dark-800/50 rounded-xl">
                    <label className="block text-dark-400 text-sm mb-2">Verification Type</label>
                    <select
                      value={captcha.type}
                      onChange={(e) => setCaptcha(prev => ({ ...prev, type: e.target.value as any }))}
                      className="w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                    >
                      <option value="button">Button Click</option>
                      <option value="math">Simple Math</option>
                      <option value="button_math">Button + Math</option>
                    </select>
                  </div>

                  <div className="p-4 bg-dark-800/50 rounded-xl">
                    <label className="block text-dark-400 text-sm mb-2">Difficulty</label>
                    <select
                      value={captcha.difficulty}
                      onChange={(e) => setCaptcha(prev => ({ ...prev, difficulty: e.target.value as any }))}
                      className="w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  <div className="p-4 bg-dark-800/50 rounded-xl">
                    <label className="block text-dark-400 text-sm mb-2">Timeout (seconds)</label>
                    <input
                      type="number"
                      value={captcha.timeout}
                      onChange={(e) => setCaptcha(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                      className="w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-xl text-white"
                    />
                  </div>
                </>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
