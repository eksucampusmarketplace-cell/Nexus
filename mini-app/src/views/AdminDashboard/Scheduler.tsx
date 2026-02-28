import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Plus, Calendar, Clock, Trash2, Play, Pause } from 'lucide-react'
import Card from '../../components/UI/Card'
import Badge from '../../components/UI/Badge'
import toast from 'react-hot-toast'

interface ScheduledMessage {
  id: string
  content: string
  schedule_type: 'once' | 'recurring'
  run_at?: string
  cron_expression?: string
  is_enabled: boolean
  run_count: number
}

const mockScheduled: ScheduledMessage[] = [
  {
    id: '1',
    content: 'Good morning everyone! ☀️',
    schedule_type: 'recurring',
    cron_expression: '0 9 * * *',
    is_enabled: true,
    run_count: 45,
  },
  {
    id: '2',
    content: 'Weekly community update...',
    schedule_type: 'once',
    run_at: '2024-03-01T10:00:00',
    is_enabled: false,
    run_count: 0,
  },
]

export default function Scheduler() {
  const { groupId } = useParams<{ groupId: string }>()
  const [messages, setMessages] = useState<ScheduledMessage[]>(mockScheduled)
  const [showAdd, setShowAdd] = useState(false)

  const toggleMessage = (id: string) => {
    setMessages(prev =>
      prev.map(m =>
        m.id === id ? { ...m, is_enabled: !m.is_enabled } : m
      )
    )
    toast.success('Schedule updated')
  }

  const deleteMessage = (id: string) => {
    setMessages(prev => prev.filter(m => m.id !== id))
    toast.success('Message deleted')
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Scheduler</h1>
          <p className="text-dark-400 mt-1">
            Schedule messages and automation
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New
        </button>
      </div>

      {/* Scheduled Messages */}
      <div className="space-y-3">
        {messages.map((message) => (
          <Card key={message.id} className="relative">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${message.is_enabled ? 'bg-green-500/10' : 'bg-dark-800'}`}>
                {message.is_enabled ? (
                  <Play className="w-5 h-5 text-green-500" />
                ) : (
                  <Pause className="w-5 h-5 text-dark-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-white truncate">
                    {message.content}
                  </p>
                  <Badge variant={message.is_enabled ? 'success' : 'default'}>
                    {message.is_enabled ? 'Active' : 'Paused'}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-dark-400">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {message.schedule_type === 'recurring'
                      ? message.cron_expression
                      : new Date(message.run_at!).toLocaleString()}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Run count: {message.run_count}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => toggleMessage(message.id)}
                  className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                >
                  {message.is_enabled ? (
                    <Pause className="w-4 h-4 text-yellow-500" />
                  ) : (
                    <Play className="w-4 h-4 text-green-500" />
                  )}
                </button>
                <button
                  onClick={() => deleteMessage(message.id)}
                  className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </button>
              </div>
            </div>
          </Card>
        ))}

        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-dark-800 rounded-full flex items-center justify-center">
              <Calendar className="w-8 h-8 text-dark-500" />
            </div>
            <p className="text-dark-400">No scheduled messages</p>
            <button
              onClick={() => setShowAdd(true)}
              className="text-primary-500 mt-2 hover:underline"
            >
              Create your first schedule
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
