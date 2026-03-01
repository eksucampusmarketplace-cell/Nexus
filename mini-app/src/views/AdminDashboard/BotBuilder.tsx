import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, Bot, GitBranch, Zap, Globe, Filter, Download, 
  ChevronRight, Play, Pause, Settings, Trash2, Copy,
  MessageSquare, Hash, Link2, Image, FileText, MoreVertical,
  Check, X, ArrowRight, Sparkles, Layers, Cpu, Send
} from 'lucide-react'
import { useGroupStore } from '../../stores/groupStore'

interface FlowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: Record<string, any>
}

interface BotFlow {
  id: number
  name: string
  description?: string
  nodes: FlowNode[]
  connections: any[]
  is_active: boolean
  is_published: boolean
}

interface UserBot {
  id: number
  name: string
  description?: string
  username?: string
  is_active: boolean
  is_published: boolean
  total_users: number
  total_messages: number
}

interface Template {
  id: number
  name: string
  description: string
  category: string
  icon: string
  usage_count: number
  is_featured: boolean
}

export default function BotBuilder() {
  const { currentGroup } = useGroupStore()
  const [activeTab, setActiveTab] = useState<'flows' | 'bots' | 'templates' | 'ai'>('bots')
  const [flows, setFlows] = useState<BotFlow[]>([])
  const [bots, setBots] = useState<UserBot[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [aiPrompt, setAiPrompt] = useState('')
  const [generatingBot, setGeneratingBot] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [flowsRes, botsRes, templatesRes] = await Promise.all([
        fetch('/api/v1/bot-builder/flows'),
        fetch('/api/v1/bot-builder/bots'),
        fetch('/api/v1/bot-builder/templates')
      ])
      const flowsData = await flowsRes.json()
      const botsData = await botsRes.json()
      const templatesData = await templatesRes.json()
      
      setFlows(flowsData.items || [])
      setBots(botsData.items || [])
      setTemplates(templatesData.items || [])
    } catch (error) {
      console.error('Error loading data:', error)
    }
    setLoading(false)
  }

  const generateBotWithAI = async () => {
    if (!aiPrompt.trim()) return
    
    setGeneratingBot(true)
    try {
      const response = await fetch('/api/v1/bot-builder/ai-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: aiPrompt,
          bot_name: `AI Bot ${bots.length + 1}`,
          description: 'Created with AI Assistant'
        })
      })
      const data = await response.json()
      setBots(prev => [data.bot, ...prev])
      setAiPrompt('')
      setActiveTab('bots')
    } catch (error) {
      console.error('Error generating bot:', error)
    }
    setGeneratingBot(false)
  }

  const createFlow = async (name: string) => {
    try {
      const response = await fetch('/api/v1/bot-builder/flows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: 'New flow',
          nodes: [],
          connections: []
        })
      })
      const newFlow = await response.json()
      setFlows(prev => [newFlow, ...prev])
      setShowCreateModal(false)
    } catch (error) {
      console.error('Error creating flow:', error)
    }
  }

  const createBot = async (name: string, type: string) => {
    try {
      const response = await fetch('/api/v1/bot-builder/bots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          bot_type: type,
          description: 'My custom bot'
        })
      })
      const newBot = await response.json()
      setBots(prev => [newBot, ...prev])
      setShowCreateModal(false)
    } catch (error) {
      console.error('Error creating bot:', error)
    }
  }

  const toggleBot = async (botId: number, isActive: boolean) => {
    try {
      await fetch(`/api/v1/bot-builder/bots/${botId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !isActive })
      })
      setBots(prev => prev.map(b => 
        b.id === botId ? { ...b, is_active: !isActive } : b
      ))
    } catch (error) {
      console.error('Error toggling bot:', error)
    }
  }

  const deleteBot = async (botId: number) => {
    if (!confirm('Are you sure you want to delete this bot?')) return
    try {
      await fetch(`/api/v1/bot-builder/bots/${botId}`, { method: 'DELETE' })
      setBots(prev => prev.filter(b => b.id !== botId))
    } catch (error) {
      console.error('Error deleting bot:', error)
    }
  }

  const useTemplate = async (templateId: number) => {
    try {
      const response = await fetch(`/api/v1/bot-builder/templates/${templateId}`)
      const template = await response.json()
      
      // Create a new flow from template
      await fetch('/api/v1/bot-builder/flows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${template.name} - My Version`,
          description: template.description,
          nodes: template.flow_data?.nodes || [],
          connections: template.flow_data?.connections || [],
          is_template: false
        })
      })
      
      setActiveTab('flows')
    } catch (error) {
      console.error('Error using template:', error)
    }
  }

  const tabs = [
    { id: 'bots', label: 'My Bots', icon: Bot },
    { id: 'flows', label: 'Flows', icon: GitBranch },
    { id: 'templates', label: 'Templates', icon: Layers },
    { id: 'ai', label: 'AI Builder', icon: Sparkles },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-primary-600/20 via-accent-500/20 to-secondary-500/20 border-b border-white/5">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMtOS45NDEgMC0xOCA4LjA1OS0xOCAxOHM4LjA1OSAxOCAxOCAxOCAxOC04LjA1OSAxOC0xOC04LjA1OS0xOC0xOC0xOHptMCAzMmMtNy43MzIgMC0xNC02LjI2OC0xNC0xNHM2LjI2OC0xNCAxNC0xNCAxNCA2LjI2OCAxNCAxNC02LjI2OCAxNC0xNCAxNHoiIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjAyIi8+PC9nPjwvc3ZnPg==')] opacity-30" />
        <div className="relative max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-400 via-accent-400 to-secondary-400 bg-clip-text text-transparent">
                Bot Builder
              </h1>
              <p className="text-dark-400 mt-2">Create powerful Telegram bots with flow builder or AI</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
              <Plus size={20} />
              Create New
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex gap-2 mt-6 overflow-x-auto pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white/10 text-white'
                    : 'text-dark-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <tab.icon size={18} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-64"
            >
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </motion.div>
          ) : (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {activeTab === 'bots' && (
                <BotsTab 
                  bots={bots} 
                  onToggle={toggleBot} 
                  onDelete={deleteBot}
                />
              )}
              {activeTab === 'flows' && (
                <FlowsTab 
                  flows={flows} 
                  onCreate={createFlow}
                />
              )}
              {activeTab === 'templates' && (
                <TemplatesTab 
                  templates={templates}
                  onUse={useTemplate}
                />
              )}
              {activeTab === 'ai' && (
                <AITab 
                  prompt={aiPrompt}
                  setPrompt={setAiPrompt}
                  generating={generatingBot}
                  onGenerate={generateBotWithAI}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <CreateModal
            onClose={() => setShowCreateModal(false)}
            onCreateFlow={createFlow}
            onCreateBot={createBot}
            activeTab={activeTab}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

function BotsTab({ bots, onToggle, onDelete }: { 
  bots: UserBot[]
  onToggle: (id: number, active: boolean) => void
  onDelete: (id: number) => void
}) {
  if (bots.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
          <Bot size={40} className="text-primary-400" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">No bots yet</h3>
        <p className="text-dark-400 mb-6">Create your first bot to get started</p>
        <p className="text-sm text-dark-500">Use the AI Builder or Templates to create a bot in seconds</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {bots.map(bot => (
        <motion.div
          key={bot.id}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:border-primary-500/30 transition-colors"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                bot.is_active 
                  ? 'bg-gradient-to-br from-primary-500 to-accent-500' 
                  : 'bg-dark-700'
              }`}>
                <Bot size={24} className="text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{bot.name}</h3>
                {bot.username && (
                  <p className="text-sm text-dark-400">@{bot.username}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => onToggle(bot.id, bot.is_active)}
                className={`p-2 rounded-lg transition-colors ${
                  bot.is_active 
                    ? 'text-green-400 hover:bg-green-400/10' 
                    : 'text-dark-400 hover:bg-dark-700'
                }`}
              >
                {bot.is_active ? <Play size={16} /> : <Pause size={16} />}
              </button>
              <button
                onClick={() => onDelete(bot.id)}
                className="p-2 rounded-lg text-dark-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
          
          {bot.description && (
            <p className="text-sm text-dark-400 mb-4 line-clamp-2">{bot.description}</p>
          )}
          
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="text-dark-500">
                <span className="text-white font-medium">{bot.total_users}</span> users
              </span>
              <span className="text-dark-500">
                <span className="text-white font-medium">{bot.total_messages}</span> msgs
              </span>
            </div>
            <span className={`px-2 py-1 rounded-md text-xs font-medium ${
              bot.is_active 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-dark-700 text-dark-400'
            }`}>
              {bot.is_active ? 'Active' : 'Stopped'}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function FlowsTab({ flows, onCreate }: { 
  flows: BotFlow[]
  onCreate: (name: string) => void
}) {
  const [newFlowName, setNewFlowName] = useState('')

  const handleCreate = () => {
    if (newFlowName.trim()) {
      onCreate(newFlowName)
      setNewFlowName('')
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <input
          type="text"
          value={newFlowName}
          onChange={(e) => setNewFlowName(e.target.value)}
          placeholder="New flow name..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500"
          onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
        />
        <button
          onClick={handleCreate}
          className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors"
        >
          Create Flow
        </button>
      </div>

      {flows.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-accent-500/20 to-secondary-500/20 flex items-center justify-center">
            <GitBranch size={40} className="text-accent-400" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No flows yet</h3>
          <p className="text-dark-400">Create a flow to build your bot's conversation logic</p>
        </div>
      ) : (
        <div className="space-y-3">
          {flows.map(flow => (
            <motion.div
              key={flow.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center justify-between bg-white/5 border border-white/10 rounded-xl p-4 hover:border-accent-500/30 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center">
                  <GitBranch size={20} className="text-accent-400" />
                </div>
                <div>
                  <h4 className="font-medium text-white">{flow.name}</h4>
                  <p className="text-sm text-dark-400">
                    {flow.nodes?.length || 0} nodes • {flow.connections?.length || 0} connections
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                  flow.is_active 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-dark-700 text-dark-400'
                }`}>
                  {flow.is_active ? 'Active' : 'Draft'}
                </span>
                <button className="p-2 rounded-lg text-dark-400 hover:text-white hover:bg-white/10 transition-colors">
                  <Settings size={18} />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}

function TemplatesTab({ templates, onUse }: { 
  templates: Template[]
  onUse: (id: number) => void
}) {
  const categories = [...new Set(templates.map(t => t.category))]
  
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'support': return MessageSquare
      case 'ecommerce': return Hash
      case 'automation': return Zap
      case 'content': return FileText
      default: return Bot
    }
  }

  return (
    <div className="space-y-8">
      {/* Featured */}
      {templates.some(t => t.is_featured) && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Sparkles size={20} className="text-accent-400" />
            Featured Templates
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.filter(t => t.is_featured).map(template => (
              <TemplateCard 
                key={template.id} 
                template={template} 
                onUse={onUse}
                getIcon={getCategoryIcon}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Templates */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">All Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(template => (
            <TemplateCard 
              key={template.id} 
              template={template} 
              onUse={onUse}
              getIcon={getCategoryIcon}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function TemplateCard({ template, onUse, getIcon }: {
  template: Template
  onUse: (id: number) => void
  getIcon: (cat: string) => any
}) {
  const Icon = getIcon(template.category)
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:border-primary-500/30 transition-all hover:scale-[1.02]"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
          <Icon size={24} className="text-primary-400" />
        </div>
        {template.is_featured && (
          <span className="px-2 py-1 bg-accent-500/20 text-accent-400 text-xs font-medium rounded-md">
            Featured
          </span>
        )}
      </div>
      
      <h4 className="font-semibold text-white mb-2">{template.name}</h4>
      <p className="text-sm text-dark-400 mb-4 line-clamp-2">{template.description}</p>
      
      <div className="flex items-center justify-between">
        <span className="text-xs text-dark-500">
          Used {template.usage_count.toLocaleString()} times
        </span>
        <button
          onClick={() => onUse(template.id)}
          className="flex items-center gap-1 text-sm text-primary-400 hover:text-primary-300 transition-colors"
        >
          Use Template
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  )
}

function AITab({ prompt, setPrompt, generating, onGenerate }: {
  prompt: string
  setPrompt: (p: string) => void
  generating: boolean
  onGenerate: () => void
}) {
  const suggestions = [
    "Create a customer support bot that answers FAQs",
    "Build a bot that sends daily news updates",
    "Make a bot that can order food from restaurants",
    "Create a bot that quizzes users on programming",
    "Build an AI assistant that can answer any question",
  ]

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-br from-primary-500/10 to-accent-500/10 border border-primary-500/20 rounded-2xl p-6 mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Sparkles size={24} className="text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">AI Bot Builder</h3>
            <p className="text-sm text-dark-400">Describe your bot in plain English</p>
          </div>
        </div>
        
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., Create a bot that helps users order pizza with custom toppings and delivers to their location..."
          className="w-full h-32 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500 resize-none"
        />
        
        <button
          onClick={onGenerate}
          disabled={!prompt.trim() || generating}
          className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-xl font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {generating ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Generating your bot...
            </>
          ) : (
            <>
              <Cpu size={20} />
              Generate Bot with AI
            </>
          )}
        </button>
      </div>

      <div>
        <h4 className="text-sm font-medium text-dark-400 mb-3">Try these suggestions</h4>
        <div className="space-y-2">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              onClick={() => setPrompt(suggestion)}
              className="w-full text-left p-3 bg-white/5 border border-white/10 rounded-xl text-dark-300 hover:bg-white/10 hover:border-primary-500/30 transition-all"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function CreateModal({ onClose, onCreateFlow, onCreateBot, activeTab }: {
  onClose: () => void
  onCreateFlow: (name: string) => void
  onCreateBot: (name: string, type: string) => void
  activeTab: string
}) {
  const [name, setName] = useState('')
  const [botType, setBotType] = useState('nexus_powered')

  const handleSubmit = () => {
    if (!name.trim()) return
    
    if (activeTab === 'flows') {
      onCreateFlow(name)
    } else {
      onCreateBot(name, botType)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-dark-800 border border-white/10 rounded-2xl p-6 w-full max-w-md"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-xl font-semibold text-white mb-4">
          Create {activeTab === 'flows' ? 'Flow' : 'Bot'}
        </h3>
        
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={`Enter ${activeTab === 'flows' ? 'flow' : 'bot'} name...`}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-dark-500 focus:outline-none focus:border-primary-500 mb-4"
          autoFocus
        />

        {activeTab === 'bots' && (
          <div className="space-y-3 mb-4">
            <button
              onClick={() => setBotType('nexus_powered')}
              className={`w-full p-4 rounded-xl border text-left transition-all ${
                botType === 'nexus_powered'
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                  <Zap size={20} className="text-primary-400" />
                </div>
                <div>
                  <h4 className="font-medium text-white">Nexus Powered</h4>
                  <p className="text-sm text-dark-400">Free bot powered by Nexus</p>
                </div>
              </div>
            </button>
            
            <button
              onClick={() => setBotType('custom')}
              className={`w-full p-4 rounded-xl border text-left transition-all ${
                botType === 'custom'
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center">
                  <Globe size={20} className="text-accent-400" />
                </div>
                <div>
                  <h4 className="font-medium text-white">Custom Token</h4>
                  <p className="text-sm text-dark-400">Use your own bot token</p>
                </div>
              </div>
            </button>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-white/5 text-white rounded-xl font-medium hover:bg-white/10 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!name.trim()}
            className="flex-1 px-4 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Create
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
