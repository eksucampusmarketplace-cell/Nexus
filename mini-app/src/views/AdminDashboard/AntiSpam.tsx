import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield,
  AlertTriangle,
  Users,
  Clock,
  Ban,
  VolumeX,
  Trash2,
  Plus,
  Search,
  Filter,
  Settings,
  Zap,
} from 'lucide-react'
import {
  getAntifloodConfig,
  updateAntifloodConfig,
  getAntiraidConfig,
  updateAntiraidConfig,
  getBannedWords,
  addBannedWord,
  removeBannedWord,
  getBannedWordListConfig,
  updateBannedWordListConfig,
} from '../../api/antispam'
import Card from '../../components/UI/Card'
import Toggle from '../../components/UI/Toggle'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

export default function AntiSpam() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'antiflood' | 'antiraid' | 'blocklist'>('antiflood')
  
  // Anti-flood state
  const [antiflood, setAntiflood] = useState({
    is_enabled: false,
    message_limit: 5,
    window_seconds: 5,
    action: 'mute',
    action_duration: 300,
    media_flood_enabled: false,
    media_limit: 3,
  })
  
  // Anti-raid state
  const [antiraid, setAntiraid] = useState({
    is_enabled: false,
    join_threshold: 10,
    window_seconds: 60,
    action: 'lock',
    auto_unlock_after: 3600,
    notify_admins: true,
  })
  
  // Blocklist state
  const [bannedWords, setBannedWords] = useState<{ id: number; word: string; list_number: number; is_regex: boolean }[]>([])
  const [list1Config, setList1Config] = useState({ action: 'delete', delete_message: true })
  const [list2Config, setList2Config] = useState({ action: 'ban', delete_message: true })
  const [newWord, setNewWord] = useState({ word: '', list_number: 1, is_regex: false })
  const [searchQuery, setSearchQuery] = useState('')

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const [flood, raid, words, config1, config2] = await Promise.all([
        getAntifloodConfig(parseInt(groupId)),
        getAntiraidConfig(parseInt(groupId)),
        getBannedWords(parseInt(groupId)),
        getBannedWordListConfig(parseInt(groupId), 1),
        getBannedWordListConfig(parseInt(groupId), 2),
      ])
      setAntiflood(flood)
      setAntiraid(raid)
      setBannedWords(words.items || words || [])
      setList1Config(config1)
      setList2Config(config2)
    } catch (error) {
      toast.error('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [groupId])

  const handleAntifloodUpdate = async (updates: Partial<typeof antiflood>) => {
    if (!groupId) return
    try {
      const updated = await updateAntifloodConfig(parseInt(groupId), updates)
      setAntiflood(updated)
      toast.success('Anti-flood settings updated')
    } catch (error) {
      toast.error('Failed to update settings')
    }
  }

  const handleAntiraidUpdate = async (updates: Partial<typeof antiraid>) => {
    if (!groupId) return
    try {
      const updated = await updateAntiraidConfig(parseInt(groupId), updates)
      setAntiraid(updated)
      toast.success('Anti-raid settings updated')
    } catch (error) {
      toast.error('Failed to update settings')
    }
  }

  const handleAddWord = async () => {
    if (!groupId || !newWord.word) return
    try {
      await addBannedWord(parseInt(groupId), newWord)
      setBannedWords([...bannedWords, { ...newWord, id: Date.now() }])
      setNewWord({ word: '', list_number: 1, is_regex: false })
      toast.success('Word added to blocklist')
    } catch (error) {
      toast.error('Failed to add word')
    }
  }

  const handleRemoveWord = async (id: number) => {
    if (!groupId) return
    try {
      await removeBannedWord(parseInt(groupId), id)
      setBannedWords(bannedWords.filter((w) => w.id !== id))
      toast.success('Word removed from blocklist')
    } catch (error) {
      toast.error('Failed to remove word')
    }
  }

  const handleListConfigUpdate = async (listNumber: number, config: typeof list1Config) => {
    if (!groupId) return
    try {
      await updateBannedWordListConfig(parseInt(groupId), listNumber, config)
      if (listNumber === 1) setList1Config(config)
      else setList2Config(config)
      toast.success('List configuration updated')
    } catch (error) {
      toast.error('Failed to update configuration')
    }
  }

  const filteredWords = bannedWords.filter((w) =>
    w.word.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Anti-Spam</h1>
        <p className="text-dark-400 mt-1">Configure spam and raid protection</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'antiflood', label: 'Anti-Flood', icon: Zap },
          { id: 'antiraid', label: 'Anti-Raid', icon: Users },
          { id: 'blocklist', label: 'Blocklist', icon: Ban },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Anti-Flood */}
      {activeTab === 'antiflood' && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white">Flood Protection</h3>
                <p className="text-dark-400 text-sm">Prevent message flooding</p>
              </div>
              <Toggle
                checked={antiflood.is_enabled}
                onChange={(checked) => handleAntifloodUpdate({ is_enabled: checked })}
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Message Limit
                </label>
                <input
                  type="number"
                  value={antiflood.message_limit}
                  onChange={(e) => handleAntifloodUpdate({ message_limit: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  disabled={!antiflood.is_enabled}
                />
                <p className="text-dark-500 text-xs mt-1">Maximum messages allowed</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Time Window (seconds)
                </label>
                <input
                  type="number"
                  value={antiflood.window_seconds}
                  onChange={(e) => handleAntifloodUpdate({ window_seconds: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  disabled={!antiflood.is_enabled}
                />
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-dark-300 mb-2">Action</label>
              <select
                value={antiflood.action}
                onChange={(e) => handleAntifloodUpdate({ action: e.target.value })}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                disabled={!antiflood.is_enabled}
              >
                <option value="delete">Delete Message</option>
                <option value="warn">Warn</option>
                <option value="mute">Mute</option>
                <option value="kick">Kick</option>
                <option value="ban">Ban</option>
              </select>
            </div>

            {antiflood.action !== 'delete' && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Duration (seconds)
                </label>
                <input
                  type="number"
                  value={antiflood.action_duration}
                  onChange={(e) => handleAntifloodUpdate({ action_duration: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  disabled={!antiflood.is_enabled}
                />
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-dark-800">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-white">Media Flood</h4>
                  <p className="text-dark-400 text-sm">Protect against media flooding</p>
                </div>
                <Toggle
                  checked={antiflood.media_flood_enabled}
                  onChange={(checked) => handleAntifloodUpdate({ media_flood_enabled: checked })}
                  disabled={!antiflood.is_enabled}
                />
              </div>
              {antiflood.media_flood_enabled && (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Media Limit
                  </label>
                  <input
                    type="number"
                    value={antiflood.media_limit}
                    onChange={(e) => handleAntifloodUpdate({ media_limit: parseInt(e.target.value) })}
                    className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  />
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Anti-Raid */}
      {activeTab === 'antiraid' && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-white">Raid Protection</h3>
                <p className="text-dark-400 text-sm">Detect and prevent raid attacks</p>
              </div>
              <Toggle
                checked={antiraid.is_enabled}
                onChange={(checked) => handleAntiraidUpdate({ is_enabled: checked })}
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Join Threshold
                </label>
                <input
                  type="number"
                  value={antiraid.join_threshold}
                  onChange={(e) => handleAntiraidUpdate({ join_threshold: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  disabled={!antiraid.is_enabled}
                />
                <p className="text-dark-500 text-xs mt-1">Joins to trigger protection</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Time Window (seconds)
                </label>
                <input
                  type="number"
                  value={antiraid.window_seconds}
                  onChange={(e) => handleAntiraidUpdate({ window_seconds: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                  disabled={!antiraid.is_enabled}
                />
              </div>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-dark-300 mb-2">Action</label>
              <select
                value={antiraid.action}
                onChange={(e) => handleAntiraidUpdate({ action: e.target.value })}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                disabled={!antiraid.is_enabled}
              >
                <option value="lock">Lock Group</option>
                <option value="restrict">Restrict New Members</option>
                <option value="ban">Ban New Joiners</option>
              </select>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Auto-Unlock After (seconds)
              </label>
              <input
                type="number"
                value={antiraid.auto_unlock_after}
                onChange={(e) => handleAntiraidUpdate({ auto_unlock_after: parseInt(e.target.value) })}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                disabled={!antiraid.is_enabled}
              />
            </div>

            <div className="mt-6 pt-6 border-t border-dark-800">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-white">Notify Admins</h4>
                  <p className="text-dark-400 text-sm">Alert when raid is detected</p>
                </div>
                <Toggle
                  checked={antiraid.notify_admins}
                  onChange={(checked) => handleAntiraidUpdate({ notify_admins: checked })}
                  disabled={!antiraid.is_enabled}
                />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Blocklist */}
      {activeTab === 'blocklist' && (
        <div className="space-y-6">
          {/* List 1 */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">List 1</h3>
                <p className="text-dark-400 text-sm">Strict filtering</p>
              </div>
              <select
                value={list1Config.action}
                onChange={(e) => handleListConfigUpdate(1, { ...list1Config, action: e.target.value })}
                className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
              >
                <option value="delete">Delete</option>
                <option value="warn">Warn</option>
                <option value="mute">Mute</option>
                <option value="kick">Kick</option>
                <option value="ban">Ban</option>
              </select>
            </div>
            <div className="flex flex-wrap gap-2">
              {filteredWords.filter((w) => w.list_number === 1).map((word) => (
                <span
                  key={word.id}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm"
                >
                  {word.is_regex ? '/ ' : ''}{word.word}
                  <button onClick={() => handleRemoveWord(word.id)} className="hover:text-red-300">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {filteredWords.filter((w) => w.list_number === 1).length === 0 && (
                <span className="text-dark-500 text-sm">No words in list</span>
              )}
            </div>
          </Card>

          {/* List 2 */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">List 2</h3>
                <p className="text-dark-400 text-sm">Less strict filtering</p>
              </div>
              <select
                value={list2Config.action}
                onChange={(e) => handleListConfigUpdate(2, { ...list2Config, action: e.target.value })}
                className="px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
              >
                <option value="delete">Delete</option>
                <option value="warn">Warn</option>
                <option value="mute">Mute</option>
                <option value="kick">Kick</option>
                <option value="ban">Ban</option>
              </select>
            </div>
            <div className="flex flex-wrap gap-2">
              {filteredWords.filter((w) => w.list_number === 2).map((word) => (
                <span
                  key={word.id}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm"
                >
                  {word.is_regex ? '/ ' : ''}{word.word}
                  <button onClick={() => handleRemoveWord(word.id)} className="hover:text-orange-300">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </span>
              ))}
              {filteredWords.filter((w) => w.list_number === 2).length === 0 && (
                <span className="text-dark-500 text-sm">No words in list</span>
              )}
            </div>
          </Card>

          {/* Add Word */}
          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Add Blocked Word</h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={newWord.word}
                onChange={(e) => setNewWord({ ...newWord, word: e.target.value })}
                placeholder="Enter word or pattern"
                className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
              />
              <select
                value={newWord.list_number}
                onChange={(e) => setNewWord({ ...newWord, list_number: parseInt(e.target.value) })}
                className="px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
              >
                <option value={1}>List 1</option>
                <option value={2}>List 2</option>
              </select>
              <label className="flex items-center gap-2 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl">
                <input
                  type="checkbox"
                  checked={newWord.is_regex}
                  onChange={(e) => setNewWord({ ...newWord, is_regex: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-dark-300 text-sm">Regex</span>
              </label>
              <button
                onClick={handleAddWord}
                disabled={!newWord.word}
                className="px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
