import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  FileText,
  MessageSquare,
  Image,
  Paperclip,
  Settings,
  Trash2,
  Send,
  Bell,
  BellOff,
} from 'lucide-react'
import { getRules, setRules, getWelcomeSettings, updateWelcomeSettings, getGoodbyeSettings, updateGoodbyeSettings } from '../../api/rules'
import Card from '../../components/UI/Card'
import Toggle from '../../components/UI/Toggle'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'
import Modal from 'react-modal'

Modal.setAppElement('#root')

const variables = [
  { code: '{first}', desc: 'User first name' },
  { code: '{last}', desc: 'User last name' },
  { code: '{fullname}', desc: 'User full name' },
  { code: '{username}', desc: 'User username' },
  { code: '{mention}', desc: 'User mention' },
  { code: '{id}', desc: 'User ID' },
  { code: '{count}', desc: 'Member count' },
  { code: '{chatname}', desc: 'Group name' },
  { code: '{rules}', desc: 'Link to rules' },
]

export default function RulesAndGreetings() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'rules' | 'welcome' | 'goodbye'>('rules')
  
  // Rules state
  const [rulesContent, setRulesContent] = useState('')
  const [rulesLoading, setRulesLoading] = useState(false)
  
  // Welcome state
  const [welcome, setWelcome] = useState({
    content: '',
    is_enabled: false,
    delete_previous: false,
    delete_after_seconds: 0,
    send_as_dm: false,
    has_buttons: false,
  })
  const [welcomeLoading, setWelcomeLoading] = useState(false)
  
  // Goodbye state
  const [goodbye, setGoodbye] = useState({
    content: '',
    is_enabled: false,
    delete_previous: false,
    has_buttons: false,
  })
  const [goodbyeLoading, setGoodbyeLoading] = useState(false)
  
  const [previewModal, setPreviewModal] = useState<{ type: string; content: string } | null>(null)

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const [rulesData, welcomeData, goodbyeData] = await Promise.all([
        getRules(parseInt(groupId)),
        getWelcomeSettings(parseInt(groupId)),
        getGoodbyeSettings(parseInt(groupId)),
      ])
      setRulesContent(rulesData.content || '')
      setWelcome(welcomeData || { content: '', is_enabled: false })
      setGoodbye(goodbyeData || { content: '', is_enabled: false })
    } catch (error) {
      // Use defaults
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [groupId])

  const handleSaveRules = async () => {
    if (!groupId) return
    setRulesLoading(true)
    try {
      await setRules(parseInt(groupId), rulesContent)
      toast.success('Rules saved')
    } catch (error) {
      toast.error('Failed to save rules')
    } finally {
      setRulesLoading(false)
    }
  }

  const handleSaveWelcome = async () => {
    if (!groupId) return
    setWelcomeLoading(true)
    try {
      await updateWelcomeSettings(parseInt(groupId), welcome)
      toast.success('Welcome settings saved')
    } catch (error) {
      toast.error('Failed to save settings')
    } finally {
      setWelcomeLoading(false)
    }
  }

  const handleSaveGoodbye = async () => {
    if (!groupId) return
    setGoodbyeLoading(true)
    try {
      await updateGoodbyeSettings(parseInt(groupId), goodbye)
      toast.success('Goodbye settings saved')
    } catch (error) {
      toast.error('Failed to save settings')
    } finally {
      setGoodbyeLoading(false)
    }
  }

  const insertVariable = (variable: string, setter: React.Dispatch<React.SetStateAction<string>>) => {
    setter((prev) => prev + variable)
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Rules & Greetings</h1>
        <p className="text-dark-400 mt-1">Configure group rules and welcome messages</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'rules', label: 'Rules', icon: FileText },
          { id: 'welcome', label: 'Welcome', icon: MessageSquare },
          { id: 'goodbye', label: 'Goodbye', icon: Bell },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Group Rules</h3>
              <button
                onClick={() => setPreviewModal({ type: 'rules', content: rulesContent })}
                className="text-primary-400 text-sm hover:text-primary-300"
              >
                Preview
              </button>
            </div>
            <textarea
              value={rulesContent}
              onChange={(e) => setRulesContent(e.target.value)}
              placeholder="Enter group rules... (Markdown supported)"
              rows={12}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 resize-none font-mono text-sm"
            />
            <div className="flex items-center justify-between mt-4">
              <p className="text-dark-500 text-sm">Supports Markdown formatting</p>
              <button
                onClick={handleSaveRules}
                disabled={rulesLoading}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white disabled:opacity-50"
              >
                {rulesLoading ? 'Saving...' : 'Save Rules'}
              </button>
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Available Variables</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {variables.map((v) => (
                <button
                  key={v.code}
                  onClick={() => insertVariable(v.code, setRulesContent)}
                  className="p-2 bg-dark-800 rounded-lg text-left hover:bg-dark-700 transition-colors"
                >
                  <code className="text-primary-400 text-sm">{v.code}</code>
                  <p className="text-dark-500 text-xs mt-1">{v.desc}</p>
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Welcome Tab */}
      {activeTab === 'welcome' && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${welcome.is_enabled ? 'bg-green-500/20' : 'bg-dark-800'}`}>
                  {welcome.is_enabled ? (
                    <Bell className="w-5 h-5 text-green-400" />
                  ) : (
                    <BellOff className="w-5 h-5 text-dark-400" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Welcome Message</h3>
                  <p className="text-dark-400 text-sm">Message sent when members join</p>
                </div>
              </div>
              <Toggle
                checked={welcome.is_enabled}
                onChange={(checked) => setWelcome({ ...welcome, is_enabled: checked })}
              />
            </div>

            <textarea
              value={welcome.content}
              onChange={(e) => setWelcome({ ...welcome, content: e.target.value })}
              placeholder="Welcome {first} to {chatname}! 🎉\n\nPlease read our rules: {rules}"
              rows={6}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 resize-none"
            />

            <div className="flex flex-wrap gap-2 mt-3">
              {variables.slice(0, 6).map((v) => (
                <button
                  key={v.code}
                  onClick={() => insertVariable(v.code, (val) => setWelcome({ ...welcome, content: welcome.content + v.code }))}
                  className="px-2 py-1 bg-dark-700 rounded text-xs text-primary-400 hover:bg-dark-600"
                >
                  {v.code}
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Welcome Settings</h3>
            <div className="space-y-4">
              <label className="flex items-center justify-between p-3 bg-dark-800 rounded-lg cursor-pointer">
                <div>
                  <span className="text-white">Delete Previous Welcome</span>
                  <p className="text-dark-400 text-sm">Remove old welcome before sending new</p>
                </div>
                <Toggle
                  checked={welcome.delete_previous}
                  onChange={(checked) => setWelcome({ ...welcome, delete_previous: checked })}
                />
              </label>

              <label className="flex items-center justify-between p-3 bg-dark-800 rounded-lg cursor-pointer">
                <div>
                  <span className="text-white">Send as DM</span>
                  <p className="text-dark-400 text-sm">Send welcome in private message</p>
                </div>
                <Toggle
                  checked={welcome.send_as_dm}
                  onChange={(checked) => setWelcome({ ...welcome, send_as_dm: checked })}
                />
              </label>

              <div>
                <label className="block text-white mb-2">Auto-Delete After (seconds, 0 = disabled)</label>
                <input
                  type="number"
                  value={welcome.delete_after_seconds}
                  onChange={(e) => setWelcome({ ...welcome, delete_after_seconds: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white"
                />
              </div>
            </div>
          </Card>

          <button
            onClick={handleSaveWelcome}
            disabled={welcomeLoading}
            className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50"
          >
            {welcomeLoading ? 'Saving...' : 'Save Welcome Settings'}
          </button>
        </div>
      )}

      {/* Goodbye Tab */}
      {activeTab === 'goodbye' && (
        <div className="space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${goodbye.is_enabled ? 'bg-green-500/20' : 'bg-dark-800'}`}>
                  {goodbye.is_enabled ? (
                    <Bell className="w-5 h-5 text-green-400" />
                  ) : (
                    <BellOff className="w-5 h-5 text-dark-400" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Goodbye Message</h3>
                  <p className="text-dark-400 text-sm">Message sent when members leave</p>
                </div>
              </div>
              <Toggle
                checked={goodbye.is_enabled}
                onChange={(checked) => setGoodbye({ ...goodbye, is_enabled: checked })}
              />
            </div>

            <textarea
              value={goodbye.content}
              onChange={(e) => setGoodbye({ ...goodbye, content: e.target.value })}
              placeholder="Goodbye {first}! 👋\nWe hope to see you again soon!"
              rows={6}
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 resize-none"
            />
          </Card>

          <button
            onClick={handleSaveGoodbye}
            disabled={goodbyeLoading}
            className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50"
          >
            {goodbyeLoading ? 'Saving...' : 'Save Goodbye Settings'}
          </button>
        </div>
      )}

      {/* Preview Modal */}
      <Modal
        isOpen={!!previewModal}
        onRequestClose={() => setPreviewModal(null)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-4">Preview</h2>
          <div className="p-4 bg-dark-800 rounded-xl text-dark-300 whitespace-pre-wrap">
            {previewModal?.content || 'No content'}
          </div>
          <button
            onClick={() => setPreviewModal(null)}
            className="mt-4 w-full py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white"
          >
            Close
          </button>
        </div>
      </Modal>
    </div>
  )
}
