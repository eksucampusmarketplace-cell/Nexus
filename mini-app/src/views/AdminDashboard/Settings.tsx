import { useParams } from 'react-router-dom'
import { Settings, Globe, Shield, Bell, Database, Bot } from 'lucide-react'
import { useState, useEffect } from 'react'
import Card from '../../components/UI/Card'
import Toggle from '../../components/UI/Toggle'
import toast from 'react-hot-toast'
import api from '../../api/client'

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'fr', name: 'French', native: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italian', native: 'Italiano', flag: '🇮🇹' },
  { code: 'es', name: 'Spanish', native: 'Español', flag: '🇪🇸' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
]

export default function SettingsPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const [language, setLanguage] = useState('en')
  const [timezone, setTimezone] = useState('UTC')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await api.get(`/groups/${groupId}`)
        if (response.data) {
          setLanguage(response.data.language || 'en')
          setTimezone(response.data.timezone || 'UTC')
        }
      } catch (error) {
        console.error('Failed to fetch group settings:', error)
      }
    }
    
    if (groupId) {
      fetchSettings()
    }
  }, [groupId])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await api.patch(`/groups/${groupId}`, {
        language,
        timezone
      })
      toast.success('Settings saved')
    } catch (error) {
      toast.error('Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-dark-400 mt-1">
          Configure your group preferences
        </p>
      </div>

      {/* General Settings */}
      <Card title="General" icon={Settings} className="mb-4">
        <div className="space-y-4 mt-4">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">
              Group Language
            </label>
            <select 
              className="select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {SUPPORTED_LANGUAGES.map(lang => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.native} ({lang.name})
                </option>
              ))}
            </select>
            <p className="text-xs text-dark-500 mt-1">
              Bot messages will be displayed in this language
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">
              Timezone
            </label>
            <select 
              className="select"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">New York (EST)</option>
              <option value="Europe/London">London (GMT)</option>
              <option value="Europe/Paris">Paris (CET)</option>
              <option value="Asia/Kolkata">India (IST)</option>
              <option value="Asia/Tokyo">Tokyo (JST)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Bot Settings */}
      <Card title="Bot Configuration" icon={Bot} className="mb-4">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-white">Custom Bot Token</p>
              <p className="text-sm text-dark-400">Use your own bot for this group</p>
            </div>
            <button className="btn-secondary text-sm">
              Configure
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-white">Delete Commands</p>
              <p className="text-sm text-dark-400">Auto-delete command messages</p>
            </div>
            <Toggle checked={true} onChange={() => {}} />
          </div>
        </div>
      </Card>

      {/* Notifications */}
      <Card title="Notifications" icon={Bell} className="mb-4">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <span className="text-dark-300">Admin Alerts</span>
            <Toggle checked={true} onChange={() => {}} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-dark-300">Daily Reports</span>
            <Toggle checked={false} onChange={() => {}} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-dark-300">New Member Alerts</span>
            <Toggle checked={true} onChange={() => {}} />
          </div>
        </div>
      </Card>

      {/* Privacy & Security */}
      <Card title="Privacy & Security" icon={Shield} className="mb-4">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-white">Log Channel</p>
              <p className="text-sm text-dark-400">Forward moderation actions</p>
            </div>
            <button className="btn-secondary text-sm">
              Set Channel
            </button>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-dark-300">Require Approval</span>
            <Toggle checked={false} onChange={() => {}} />
          </div>
        </div>
      </Card>

      {/* Data */}
      <Card title="Data Management" icon={Database}>
        <div className="space-y-3 mt-4">
          <button className="w-full btn-secondary flex items-center justify-center gap-2">
            Export Group Data
          </button>
          <button className="w-full btn-secondary flex items-center justify-center gap-2">
            Import Settings
          </button>
          <button className="w-full btn-danger flex items-center justify-center gap-2">
            Reset All Settings
          </button>
        </div>
      </Card>

      {/* Save Button */}
      <div className="mt-6">
        <button 
          onClick={handleSave} 
          className="w-full btn-primary"
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
