import { useParams } from 'react-router-dom'
import { Settings, Globe, Shield, Bell, Database, Bot } from 'lucide-react'
import Card from '../../components/UI/Card'
import Toggle from '../../components/UI/Toggle'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { groupId } = useParams<{ groupId: string }>()

  const handleSave = () => {
    toast.success('Settings saved')
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
            <select className="select">
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="ru">Russian</option>
              <option value="ar">Arabic</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1">
              Timezone
            </label>
            <select className="select">
              <option value="UTC">UTC</option>
              <option value="America/New_York">New York (EST)</option>
              <option value="Europe/London">London (GMT)</option>
              <option value="Europe/Paris">Paris (CET)</option>
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
        <button onClick={handleSave} className="w-full btn-primary">
          Save Changes
        </button>
      </div>
    </div>
  )
}
