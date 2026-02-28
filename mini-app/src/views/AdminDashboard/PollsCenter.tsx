import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  BarChart3,
  Plus,
  Vote,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  Trash2,
  History,
  Settings,
  Poll as PollIcon,
  GripVertical,
  TrendingUp,
  Calendar,
} from 'lucide-react'
import { getPolls, getPoll, createPoll, closePoll, deletePoll, getPollStats, PollWithResults, PollStats } from '../../api/polls'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import toast from 'react-hot-toast'

Modal.setAppElement('#root')

interface Poll {
  id: number
  question: string
  options: string[]
  is_anonymous: boolean
  allows_multiple: boolean
  is_closed: boolean
  created_at: string
  total_votes: number
}

export default function PollsCenter() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'active' | 'closed' | 'create'>('active')
  const [polls, setPolls] = useState<Poll[]>([])
  const [stats, setStats] = useState<PollStats | null>(null)
  const [selectedPoll, setSelectedPoll] = useState<PollWithResults | null>(null)
  
  // Create poll form
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [pollQuestion, setPollQuestion] = useState('')
  const [pollOptions, setPollOptions] = useState<string[]>(['', ''])
  const [pollType, setPollType] = useState<'regular' | 'quiz' | 'straw'>('regular')
  const [isAnonymous, setIsAnonymous] = useState(false)
  const [allowsMultiple, setAllowsMultiple] = useState(false)
  const [creating, setCreating] = useState(false)

  const loadPolls = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const includeClosed = activeTab === 'closed'
      const response = await getPolls(parseInt(groupId), 1, 20, includeClosed)
      setPolls(response.items || [])
    } catch (error) {
      console.error('Failed to load polls:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    if (!groupId) return
    try {
      const response = await getPollStats(parseInt(groupId))
      setStats(response)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  useEffect(() => {
    loadPolls()
  }, [groupId, activeTab])

  useEffect(() => {
    loadStats()
  }, [groupId])

  const handleViewPoll = async (pollId: number) => {
    if (!groupId) return
    try {
      const response = await getPoll(parseInt(groupId), pollId)
      setSelectedPoll(response)
    } catch (error) {
      console.error('Failed to load poll:', error)
    }
  }

  const handleCreatePoll = async () => {
    if (!groupId || !pollQuestion || pollOptions.filter(o => o.trim()).length < 2) return
    
    setCreating(true)
    try {
      await createPoll(parseInt(groupId), {
        question: pollQuestion,
        options: pollOptions.filter(o => o.trim()),
        poll_type: pollType,
        is_anonymous: isAnonymous,
        allows_multiple: allowsMultiple,
      })
      toast.success('Poll created!')
      setCreateModalOpen(false)
      setPollQuestion('')
      setPollOptions(['', ''])
      loadPolls()
      loadStats()
    } catch (error) {
      console.error('Failed to create poll:', error)
      toast.error('Failed to create poll')
    } finally {
      setCreating(false)
    }
  }

  const handleClosePoll = async (pollId: number) => {
    if (!groupId || !confirm('Close this poll?')) return
    
    try {
      await closePoll(parseInt(groupId), pollId)
      toast.success('Poll closed')
      loadPolls()
      loadStats()
    } catch (error) {
      console.error('Failed to close poll:', error)
    }
  }

  const handleDeletePoll = async (pollId: number) => {
    if (!groupId || !confirm('Delete this poll permanently?')) return
    
    try {
      await deletePoll(parseInt(groupId), pollId)
      toast.success('Poll deleted')
      loadPolls()
      loadStats()
    } catch (error) {
      console.error('Failed to delete poll:', error)
    }
  }

  const addOption = () => {
    if (pollOptions.length < 10) {
      setPollOptions([...pollOptions, ''])
    }
  }

  const removeOption = (index: number) => {
    if (pollOptions.length > 2) {
      setPollOptions(pollOptions.filter((_, i) => i !== index))
    }
  }

  const updateOption = (index: number, value: string) => {
    const newOptions = [...pollOptions]
    newOptions[index] = value
    setPollOptions(newOptions)
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Polls Center</h1>
          <p className="text-dark-400 mt-1">Create and manage polls</p>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Poll
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard
            title="Total Polls"
            value={stats.total_polls}
            icon={PollIcon}
          />
          <StatCard
            title="Active"
            value={stats.active_polls}
            icon={Vote}
          />
          <StatCard
            title="Closed"
            value={stats.closed_polls}
            icon={CheckCircle}
          />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('active')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'active'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <Vote className="w-4 h-4 inline mr-2" />
          Active
        </button>
        <button
          onClick={() => setActiveTab('closed')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'closed'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <History className="w-4 h-4 inline mr-2" />
          Closed
        </button>
      </div>

      {/* Polls List */}
      <div className="space-y-4">
        {polls.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <PollIcon className="w-16 h-16 text-dark-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-dark-300">
                No {activeTab} polls
              </h3>
              <p className="text-dark-500 mt-1">
                {activeTab === 'active' ? 'Create a poll to get started' : 'Closed polls will appear here'}
              </p>
            </div>
          </Card>
        ) : (
          polls.map(poll => (
            <Card key={poll.id} className="hover:border-dark-700 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      poll.is_closed 
                        ? 'bg-dark-700 text-dark-400' 
                        : 'bg-green-500/20 text-green-400'
                    }`}>
                      {poll.is_closed ? 'Closed' : 'Active'}
                    </span>
                    {poll.is_anonymous && (
                      <span className="px-2 py-0.5 bg-purple-500/20 rounded text-xs text-purple-400">
                        Anonymous
                      </span>
                    )}
                    {poll.allows_multiple && (
                      <span className="px-2 py-0.5 bg-blue-500/20 rounded text-xs text-blue-400">
                        Multi-select
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-3">
                    {poll.question}
                  </h3>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {poll.options.slice(0, 4).map((opt, i) => (
                      <span key={i} className="px-3 py-1 bg-dark-800 rounded-full text-sm text-dark-300">
                        {opt}
                      </span>
                    ))}
                    {poll.options.length > 4 && (
                      <span className="px-3 py-1 bg-dark-800 rounded-full text-sm text-dark-400">
                        +{poll.options.length - 4} more
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-dark-500">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {poll.total_votes} votes
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(poll.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleViewPoll(poll.id)}
                    className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    title="View Results"
                  >
                    <BarChart3 className="w-5 h-5 text-primary-400" />
                  </button>
                  {!poll.is_closed && (
                    <button
                      onClick={() => handleClosePoll(poll.id)}
                      className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                      title="Close Poll"
                    >
                      <XCircle className="w-5 h-5 text-yellow-400" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDeletePoll(poll.id)}
                    className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-5 h-5 text-red-400" />
                  </button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Create Poll Modal */}
      <Modal
        isOpen={createModalOpen}
        onRequestClose={() => setCreateModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Create Poll</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Question
              </label>
              <input
                type="text"
                value={pollQuestion}
                onChange={(e) => setPollQuestion(e.target.value)}
                placeholder="What would you like to ask?"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Options
              </label>
              <div className="space-y-2">
                {pollOptions.map((option, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={option}
                      onChange={(e) => updateOption(index, e.target.value)}
                      placeholder={`Option ${index + 1}`}
                      className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                    />
                    {pollOptions.length > 2 && (
                      <button
                        onClick={() => removeOption(index)}
                        className="p-2 text-red-400 hover:bg-dark-800 rounded-lg"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              {pollOptions.length < 10 && (
                <button
                  onClick={addOption}
                  className="mt-2 text-primary-400 hover:text-primary-300 text-sm"
                >
                  + Add Option
                </button>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Poll Type
              </label>
              <select
                value={pollType}
                onChange={(e) => setPollType(e.target.value as any)}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="regular">Regular Poll</option>
                <option value="quiz">Quiz (with correct answer)</option>
                <option value="straw">Straw Poll (quick vote)</option>
              </select>
            </div>

            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-dark-300">Anonymous</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowsMultiple}
                  onChange={(e) => setAllowsMultiple(e.target.checked)}
                  className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-dark-300">Allow Multiple Choices</span>
              </label>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setCreateModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreatePoll}
              disabled={creating || !pollQuestion || pollOptions.filter(o => o.trim()).length < 2}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Create Poll
            </button>
          </div>
        </div>
      </Modal>

      {/* Poll Results Modal */}
      <Modal
        isOpen={!!selectedPoll}
        onRequestClose={() => setSelectedPoll(null)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        {selectedPoll && (
          <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg border border-dark-800">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-white">{selectedPoll.question}</h2>
                <p className="text-dark-400 text-sm mt-1">
                  {selectedPoll.total_votes} total votes • {selectedPoll.is_closed ? 'Closed' : 'Active'}
                </p>
              </div>
              <button
                onClick={() => setSelectedPoll(null)}
                className="p-2 hover:bg-dark-800 rounded-lg"
              >
                <XCircle className="w-5 h-5 text-dark-400" />
              </button>
            </div>

            <div className="space-y-3">
              {selectedPoll.options_with_counts.map((option, index) => {
                const percentage = selectedPoll.total_votes > 0 
                  ? (option.voter_count / selectedPoll.total_votes * 100).toFixed(1)
                  : '0'
                
                return (
                  <div key={index} className="relative">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white">{option.text}</span>
                      <span className="text-dark-400 text-sm">
                        {option.voter_count} votes ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary-500 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setSelectedPoll(null)}
                className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
