import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Workflow,
  MessageSquare,
  Zap,
  Clock,
  Settings,
  Plus,
  Trash2,
  Edit3,
  Play,
  Pause,
  Check,
  X,
  ChevronRight,
  Terminal,
  Hash,
  AlertCircle,
  Activity,
  Bot,
  Send,
  UserX,
  Shield,
  Hourglass,
  GitBranch,
  Globe,
  Terminal as TerminalIcon,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as automationAPI from '../../api/automation'

Modal.setAppElement('#root')

type TabType = 'workflows' | 'responders' | 'commands' | 'logs' | 'stats'

const TRIGGER_ICONS: Record<string, any> = {
  keyword: Hash,
  command: Terminal,
  schedule: Clock,
  event: Zap,
  new_member: UserX,
  message: MessageSquare,
}

const ACTION_ICONS: Record<string, any> = {
  send_message: Send,
  delete_message: Trash2,
  warn_user: AlertCircle,
  mute_user: Shield,
  kick_user: UserX,
  assign_role: Bot,
  send_dm: MessageSquare,
  wait: Hourglass,
  condition: GitBranch,
  http_request: Globe,
}

export default function AutomationCenter() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('workflows')
  const [workflows, setWorkflows] = useState<automationAPI.Workflow[]>([])
  const [responders, setResponders] = useState<automationAPI.KeywordResponder[]>([])
  const [commands, setCommands] = useState<automationAPI.CustomCommand[]>([])
  const [logs, setLogs] = useState<automationAPI.TriggerLog[]>([])
  const [stats, setStats] = useState<automationAPI.AutomationStats | null>(null)
  
  // Modal states
  const [workflowModalOpen, setWorkflowModalOpen] = useState(false)
  const [responderModalOpen, setResponderModalOpen] = useState(false)
  const [commandModalOpen, setCommandModalOpen] = useState(false)
  const [testModalOpen, setTestModalOpen] = useState(false)
  
  // Form states
  const [workflowForm, setWorkflowForm] = useState({
    name: '',
    description: '',
    trigger_type: 'keyword' as const,
    trigger_config: {},
    actions: [] as automationAPI.WorkflowAction[]
  })
  const [responderForm, setResponderForm] = useState({
    keywords: [] as string[],
    match_type: 'contains' as const,
    case_sensitive: false,
    responses: [''],
    random_response: true,
    delete_trigger: false,
    cooldown_seconds: 0
  })
  const [commandForm, setCommandForm] = useState({
    command: '',
    description: '',
    response_type: 'text' as const,
    response_content: '',
    allow_variables: true,
    require_args: false,
    admin_only: false
  })
  const [newKeyword, setNewKeyword] = useState('')
  const [testInput, setTestInput] = useState('')

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'workflows':
          const workflowsRes = await automationAPI.getWorkflows(parseInt(groupId))
          setWorkflows(workflowsRes)
          break
        case 'responders':
          const respondersRes = await automationAPI.getKeywordResponders(parseInt(groupId))
          setResponders(respondersRes)
          break
        case 'commands':
          const commandsRes = await automationAPI.getCustomCommands(parseInt(groupId))
          setCommands(commandsRes)
          break
        case 'logs':
          const logsRes = await automationAPI.getTriggerLogs(parseInt(groupId), 100)
          setLogs(logsRes)
          break
        case 'stats':
          const statsRes = await automationAPI.getAutomationStats(parseInt(groupId))
          setStats(statsRes)
          break
      }
    } catch (error) {
      console.error('Failed to load automation data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateWorkflow = async () => {
    if (!groupId || !workflowForm.name) return
    try {
      await automationAPI.createWorkflow(parseInt(groupId), workflowForm)
      toast.success('Workflow created!')
      setWorkflowModalOpen(false)
      setWorkflowForm({
        name: '',
        description: '',
        trigger_type: 'keyword',
        trigger_config: {},
        actions: []
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create workflow')
    }
  }

  const handleCreateResponder = async () => {
    if (!groupId || responderForm.keywords.length === 0 || responderForm.responses[0] === '') return
    try {
      await automationAPI.createKeywordResponder(parseInt(groupId), responderForm)
      toast.success('Responder created!')
      setResponderModalOpen(false)
      setResponderForm({
        keywords: [],
        match_type: 'contains',
        case_sensitive: false,
        responses: [''],
        random_response: true,
        delete_trigger: false,
        cooldown_seconds: 0
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create responder')
    }
  }

  const handleCreateCommand = async () => {
    if (!groupId || !commandForm.command || !commandForm.response_content) return
    try {
      await automationAPI.createCustomCommand(parseInt(groupId), commandForm)
      toast.success('Command created!')
      setCommandModalOpen(false)
      setCommandForm({
        command: '',
        description: '',
        response_type: 'text',
        response_content: '',
        allow_variables: true,
        require_args: false,
        admin_only: false
      })
      loadData()
    } catch (error) {
      toast.error('Failed to create command')
    }
  }

  const toggleWorkflow = async (workflow: automationAPI.Workflow) => {
    if (!groupId) return
    try {
      await automationAPI.toggleWorkflow(parseInt(groupId), workflow.id, !workflow.is_enabled)
      toast.success(workflow.is_enabled ? 'Workflow disabled' : 'Workflow enabled')
      loadData()
    } catch (error) {
      toast.error('Failed to toggle workflow')
    }
  }

  const deleteWorkflow = async (workflowId: number) => {
    if (!groupId || !confirm('Delete this workflow?')) return
    try {
      await automationAPI.deleteWorkflow(parseInt(groupId), workflowId)
      toast.success('Workflow deleted')
      loadData()
    } catch (error) {
      toast.error('Failed to delete')
    }
  }

  const addKeyword = () => {
    if (newKeyword && !responderForm.keywords.includes(newKeyword)) {
      setResponderForm(prev => ({ ...prev, keywords: [...prev.keywords, newKeyword] }))
      setNewKeyword('')
    }
  }

  const removeKeyword = (keyword: string) => {
    setResponderForm(prev => ({ ...prev, keywords: prev.keywords.filter(k => k !== keyword) }))
  }

  const addResponse = () => {
    setResponderForm(prev => ({ ...prev, responses: [...prev.responses, ''] }))
  }

  const updateResponse = (index: number, value: string) => {
    setResponderForm(prev => ({
      ...prev,
      responses: prev.responses.map((r, i) => i === index ? value : r)
    }))
  }

  const removeResponse = (index: number) => {
    if (responderForm.responses.length > 1) {
      setResponderForm(prev => ({
        ...prev,
        responses: prev.responses.filter((_, i) => i !== index)
      }))
    }
  }

  if (loading && !workflows.length) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl flex items-center justify-center">
            <Workflow className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Automation Center</h1>
            <p className="text-dark-400 mt-1">Workflows, triggers, and auto-responders</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'workflows', label: 'Workflows', icon: Workflow },
          { id: 'responders', label: 'Auto-Responders', icon: MessageSquare },
          { id: 'commands', label: 'Custom Commands', icon: Terminal },
          { id: 'logs', label: 'Trigger Logs', icon: Activity },
          { id: 'stats', label: 'Statistics', icon: Zap },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Workflows Tab */}
      {activeTab === 'workflows' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Automation Workflows</h3>
            <button
              onClick={() => setWorkflowModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Workflow
            </button>
          </div>

          <div className="grid gap-4">
            {workflows.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <Workflow className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No workflows yet</p>
                  <p className="text-sm text-dark-500 mt-1">Create automated workflows to handle events</p>
                </div>
              </Card>
            ) : (
              workflows.map(workflow => {
                const TriggerIcon = TRIGGER_ICONS[workflow.trigger_type] || Zap
                return (
                  <Card key={workflow.id} className={workflow.is_enabled ? '' : 'opacity-60'}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          workflow.is_enabled
                            ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20'
                            : 'bg-dark-800'
                        }`}>
                          <TriggerIcon className={`w-6 h-6 ${workflow.is_enabled ? 'text-purple-400' : 'text-dark-500'}`} />
                        </div>
                        <div>
                          <h4 className="font-semibold text-white">{workflow.name}</h4>
                          {workflow.description && (
                            <p className="text-sm text-dark-400">{workflow.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-sm text-dark-400">
                            <span className="flex items-center gap-1">
                              <Zap className="w-3 h-3" />
                              {workflow.trigger_type}
                            </span>
                            <span className="flex items-center gap-1">
                              <Play className="w-3 h-3" />
                              {workflow.run_count} runs
                            </span>
                            {workflow.last_run_at && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                Last: {new Date(workflow.last_run_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => toggleWorkflow(workflow)}
                          className={`p-2 rounded-lg transition-colors ${
                            workflow.is_enabled
                              ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
                          }`}
                        >
                          {workflow.is_enabled ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => deleteWorkflow(workflow.id)}
                          className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    </div>

                    {/* Actions Preview */}
                    {workflow.actions.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-dark-800">
                        <p className="text-xs text-dark-500 mb-2">Actions:</p>
                        <div className="flex flex-wrap gap-2">
                          {workflow.actions.map((action, i) => {
                            const ActionIcon = ACTION_ICONS[action.type] || Zap
                            return (
                              <div key={i} className="flex items-center gap-1 px-2 py-1 bg-dark-800/50 rounded-lg text-sm text-dark-300">
                                <ActionIcon className="w-3 h-3" />
                                {action.type.replace('_', ' ')}
                                {action.delay_seconds && (
                                  <span className="text-dark-500">(+{action.delay_seconds}s)</span>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </Card>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* Responders Tab */}
      {activeTab === 'responders' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Keyword Auto-Responders</h3>
            <button
              onClick={() => setResponderModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Responder
            </button>
          </div>

          <div className="grid gap-4">
            {responders.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <MessageSquare className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No auto-responders yet</p>
                  <p className="text-sm text-dark-500 mt-1">Create keyword triggers for automatic responses</p>
                </div>
              </Card>
            ) : (
              responders.map(responder => (
                <Card key={responder.id} className={responder.is_active ? '' : 'opacity-60'}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          responder.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-dark-700 text-dark-400'
                        }`}>
                          {responder.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <span className="px-2 py-0.5 bg-dark-800 rounded text-xs text-dark-400">
                          {responder.match_type}
                        </span>
                        {responder.case_sensitive && (
                          <span className="px-2 py-0.5 bg-yellow-500/20 rounded text-xs text-yellow-400">
                            Case Sensitive
                          </span>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap gap-1 mb-3">
                        {responder.keywords.map(keyword => (
                          <span key={keyword} className="px-2 py-1 bg-purple-500/20 rounded-lg text-sm text-purple-400">
                            {keyword}
                          </span>
                        ))}
                      </div>

                      <div className="space-y-2">
                        {responder.responses.slice(0, 2).map((response, i) => (
                          <p key={i} className="text-sm text-dark-400 line-clamp-1">
                            → {response}
                          </p>
                        ))}
                        {responder.responses.length > 2 && (
                          <p className="text-xs text-dark-500">
                            +{responder.responses.length - 2} more responses
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-4 mt-3 text-sm text-dark-500">
                        <span>Triggered {responder.trigger_count} times</span>
                        {responder.cooldown_seconds > 0 && (
                          <span>Cooldown: {responder.cooldown_seconds}s</span>
                        )}
                        {responder.delete_trigger && <span>Deletes trigger</span>}
                      </div>
                    </div>

                    <div className="flex gap-1 ml-4">
                      <button
                        onClick={() => {
                          // Test responder
                        }}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Play className="w-4 h-4 text-primary-400" />
                      </button>
                      <button
                        onClick={() => {/* Edit */}}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Edit3 className="w-4 h-4 text-dark-400" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Commands Tab */}
      {activeTab === 'commands' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Custom Commands</h3>
            <button
              onClick={() => setCommandModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Command
            </button>
          </div>

          <div className="grid gap-4">
            {commands.length === 0 ? (
              <Card>
                <div className="text-center py-12">
                  <Terminal className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No custom commands yet</p>
                  <p className="text-sm text-dark-500 mt-1">Create /commands for your group</p>
                </div>
              </Card>
            ) : (
              commands.map(cmd => (
                <Card key={cmd.id} className={cmd.is_active ? '' : 'opacity-60'}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <code className="px-2 py-1 bg-dark-800 rounded text-primary-400">/{cmd.command}</code>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          cmd.is_active
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-dark-700 text-dark-400'
                        }`}>
                          {cmd.is_active ? 'Active' : 'Inactive'}
                        </span>
                        {cmd.admin_only && (
                          <span className="px-2 py-0.5 bg-red-500/20 rounded text-xs text-red-400">
                            Admin Only
                          </span>
                        )}
                      </div>
                      
                      {cmd.description && (
                        <p className="text-sm text-dark-400 mb-2">{cmd.description}</p>
                      )}

                      <p className="text-sm text-dark-500 line-clamp-2">{cmd.response_content}</p>

                      <div className="flex items-center gap-4 mt-3 text-sm text-dark-500">
                        <span>Used {cmd.usage_count} times</span>
                        {cmd.allow_variables && <span>Variables enabled</span>}
                        {cmd.require_args && <span>Requires arguments</span>}
                      </div>
                    </div>

                    <div className="flex gap-1 ml-4">
                      <button
                        onClick={() => {/* Edit */}}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Edit3 className="w-4 h-4 text-dark-400" />
                      </button>
                      <button
                        onClick={() => {/* Delete */}}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <Card title="Trigger Logs" icon={Activity}>
          <div className="space-y-2 mt-4 max-h-[500px] overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-dark-400 text-center py-8">No logs yet</p>
            ) : (
              logs.map(log => (
                <div
                  key={log.id}
                  className={`flex items-center gap-3 p-3 rounded-xl ${
                    log.success ? 'bg-dark-800/30' : 'bg-red-500/10'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    log.success ? 'bg-green-500/20' : 'bg-red-500/20'
                  }`}>
                    {log.success ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <X className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm">{log.trigger_type}</p>
                    <p className="text-xs text-dark-400">
                      {log.actions_executed} actions executed
                      {log.error && <span className="text-red-400 ml-2">• {log.error}</span>}
                    </p>
                  </div>
                  <span className="text-xs text-dark-500">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Total Workflows" value={stats.total_workflows} icon={Workflow} />
            <StatCard title="Active Workflows" value={stats.active_workflows} icon={Zap} />
            <StatCard title="Keyword Responders" value={stats.keyword_responders} icon={MessageSquare} />
            <StatCard title="Custom Commands" value={stats.custom_commands} icon={Terminal} />
          </div>

          <Card title="Top Triggers" icon={Activity}>
            <div className="space-y-3 mt-4">
              {stats.top_triggers.map((trigger, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                  <span className="text-white">{trigger.name}</span>
                  <span className="text-primary-400 font-medium">{trigger.count} triggers</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Workflow Modal */}
      <Modal
        isOpen={workflowModalOpen}
        onRequestClose={() => setWorkflowModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">New Workflow</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Workflow Name</label>
              <input
                type="text"
                value={workflowForm.name}
                onChange={(e) => setWorkflowForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Welcome New Members"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Description (optional)</label>
              <textarea
                value={workflowForm.description}
                onChange={(e) => setWorkflowForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="What does this workflow do?"
                rows={2}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Trigger Type</label>
              <select
                value={workflowForm.trigger_type}
                onChange={(e) => setWorkflowForm(prev => ({ ...prev, trigger_type: e.target.value as any }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="keyword">Keyword</option>
                <option value="command">Command</option>
                <option value="schedule">Schedule</option>
                <option value="event">Event</option>
                <option value="new_member">New Member</option>
                <option value="message">Any Message</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setWorkflowModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateWorkflow}
              disabled={!workflowForm.name}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Workflow
            </button>
          </div>
        </div>
      </Modal>

      {/* Responder Modal */}
      <Modal
        isOpen={responderModalOpen}
        onRequestClose={() => setResponderModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">New Auto-Responder</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Keywords</label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                  placeholder="Add a keyword"
                  className="flex-1 px-4 py-2 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                />
                <button
                  onClick={addKeyword}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {responderForm.keywords.map(keyword => (
                  <span key={keyword} className="flex items-center gap-1 px-3 py-1 bg-purple-500/20 rounded-full text-sm text-purple-400">
                    {keyword}
                    <button onClick={() => removeKeyword(keyword)} className="hover:text-purple-300">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Match Type</label>
              <select
                value={responderForm.match_type}
                onChange={(e) => setResponderForm(prev => ({ ...prev, match_type: e.target.value as any }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="contains">Contains</option>
                <option value="exact">Exact Match</option>
                <option value="starts_with">Starts With</option>
                <option value="regex">Regex</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Responses</label>
              <div className="space-y-2">
                {responderForm.responses.map((response, index) => (
                  <div key={index} className="flex gap-2">
                    <textarea
                      value={response}
                      onChange={(e) => updateResponse(index, e.target.value)}
                      placeholder={`Response ${index + 1}`}
                      rows={2}
                      className="flex-1 px-4 py-2 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
                    />
                    {responderForm.responses.length > 1 && (
                      <button
                        onClick={() => removeResponse(index)}
                        className="p-2 hover:bg-dark-800 rounded-xl transition-colors"
                      >
                        <X className="w-4 h-4 text-red-400" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={addResponse}
                className="mt-2 text-primary-400 hover:text-primary-300 text-sm"
              >
                + Add Another Response
              </button>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={responderForm.random_response}
                onChange={(e) => setResponderForm(prev => ({ ...prev, random_response: e.target.checked }))}
                className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
              />
              <span className="text-sm text-dark-300">Random response (pick one)</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={responderForm.delete_trigger}
                onChange={(e) => setResponderForm(prev => ({ ...prev, delete_trigger: e.target.checked }))}
                className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
              />
              <span className="text-sm text-dark-300">Delete trigger message</span>
            </label>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setResponderModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateResponder}
              disabled={responderForm.keywords.length === 0 || responderForm.responses[0] === ''}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Responder
            </button>
          </div>
        </div>
      </Modal>

      {/* Command Modal */}
      <Modal
        isOpen={commandModalOpen}
        onRequestClose={() => setCommandModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">New Custom Command</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Command</label>
              <div className="flex items-center gap-2">
                <span className="text-dark-500">/</span>
                <input
                  type="text"
                  value={commandForm.command}
                  onChange={(e) => setCommandForm(prev => ({ ...prev, command: e.target.value.replace(/\s/g, '') }))}
                  placeholder="commandname"
                  className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Description</label>
              <input
                type="text"
                value={commandForm.description}
                onChange={(e) => setCommandForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="What does this command do?"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Response</label>
              <textarea
                value={commandForm.response_content}
                onChange={(e) => setCommandForm(prev => ({ ...prev, response_content: e.target.value }))}
                placeholder="What should the bot reply with?"
                rows={4}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={commandForm.admin_only}
                  onChange={(e) => setCommandForm(prev => ({ ...prev, admin_only: e.target.checked }))}
                  className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
                />
                <span className="text-sm text-dark-300">Admin only</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={commandForm.allow_variables}
                  onChange={(e) => setCommandForm(prev => ({ ...prev, allow_variables: e.target.checked }))}
                  className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
                />
                <span className="text-sm text-dark-300">Allow variables ({'{user}'}, {'{group}'}, etc.)</span>
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setCommandModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateCommand}
              disabled={!commandForm.command || !commandForm.response_content}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Command
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
