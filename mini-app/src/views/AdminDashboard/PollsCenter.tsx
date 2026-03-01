import { useState } from 'react'
import { BarChart3, PlusCircle, CheckSquare, Users } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'
import Toggle from '../../components/UI/Toggle'

const mockPolls = [
  { id: 1, question: 'What is your favourite programming language?', votes: 124, status: 'active', options: ['Python', 'TypeScript', 'Rust', 'Go'] },
  { id: 2, question: 'Best time for weekly group calls?', votes: 87, status: 'closed', options: ['Monday', 'Wednesday', 'Friday', 'Weekend'] },
  { id: 3, question: 'Should we add a games channel?', votes: 56, status: 'active', options: ['Yes', 'No', 'Maybe'] },
]

export default function PollsCenter() {
  const [anonymousPolls, setAnonymousPolls] = useState(true)
  const [multipleChoice, setMultipleChoice] = useState(false)
  const [quizMode, setQuizMode] = useState(false)

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Polls Center</h1>
        <p className="text-dark-400 mt-1">
          Create and manage polls and quizzes
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Active Polls"
          value="2"
          icon={BarChart3}
        />
        <StatCard
          title="Total Votes"
          value="267"
          icon={Users}
        />
      </div>

      {/* Poll Settings */}
      <Card title="Poll Settings" icon={CheckSquare} className="mb-6">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">Anonymous Polls</p>
              <p className="text-dark-400 text-xs">Hide voter identities</p>
            </div>
            <Toggle checked={anonymousPolls} onChange={setAnonymousPolls} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">Multiple Choice</p>
              <p className="text-dark-400 text-xs">Allow selecting multiple options</p>
            </div>
            <Toggle checked={multipleChoice} onChange={setMultipleChoice} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">Quiz Mode</p>
              <p className="text-dark-400 text-xs">Reveal correct answer after voting</p>
            </div>
            <Toggle checked={quizMode} onChange={setQuizMode} />
          </div>
        </div>
      </Card>

      {/* Polls List */}
      <Card title="Recent Polls" icon={BarChart3}>
        <div className="space-y-4 mt-4">
          {mockPolls.map((poll) => (
            <div key={poll.id} className="bg-dark-800 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3 mb-3">
                <p className="text-white text-sm font-medium flex-1">{poll.question}</p>
                <Badge variant={poll.status === 'active' ? 'success' : 'default'}>
                  {poll.status === 'active' ? 'Active' : 'Closed'}
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-dark-400 text-xs">
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {poll.votes} votes
                </span>
                <span className="flex items-center gap-1">
                  <CheckSquare className="w-3 h-3" />
                  {poll.options.length} options
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-1">
                {poll.options.map((opt) => (
                  <span key={opt} className="text-xs bg-dark-700 text-dark-300 px-2 py-0.5 rounded-full">
                    {opt}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-dark-700">
          <p className="text-dark-400 text-sm text-center">
            Use <code className="text-primary-400">/poll</code> or <code className="text-primary-400">/quiz</code> in the group to create polls
          </p>
        </div>
      </Card>
    </div>
  )
}
