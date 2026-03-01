import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Megaphone, Send, Clock, Users, CheckCircle, AlertCircle } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Toggle from '../../components/UI/Toggle'
import toast from 'react-hot-toast'

const mockHistory = [
  { id: 1, message: 'Welcome to our new announcement channel! 🎉', sentAt: '2024-01-15 10:00', recipients: 1240, status: 'sent' },
  { id: 2, message: 'Group maintenance scheduled for tomorrow at 2PM UTC.', sentAt: '2024-01-14 16:30', recipients: 1235, status: 'sent' },
  { id: 3, message: 'New rules have been published. Please read the pinned message.', sentAt: '2024-01-13 09:15', recipients: 1220, status: 'sent' },
]

export default function BroadcastCenter() {
  const { groupId } = useParams<{ groupId: string }>()
  const [message, setMessage] = useState('')
  const [pinMessage, setPinMessage] = useState(false)
  const [silentSend, setSilentSend] = useState(false)
  const [scheduleEnabled, setScheduleEnabled] = useState(false)
  const [scheduledTime, setScheduledTime] = useState('')
  const [sending, setSending] = useState(false)

  const handleBroadcast = async () => {
    if (!message.trim()) {
      toast.error('Please enter a message')
      return
    }
    setSending(true)
    try {
      await new Promise(r => setTimeout(r, 1000))
      toast.success(scheduleEnabled ? 'Broadcast scheduled!' : 'Broadcast sent!')
      setMessage('')
    } catch {
      toast.error('Failed to send broadcast')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Broadcast Center</h1>
        <p className="text-dark-400 mt-1">Send announcements to all group members</p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard title="Total Broadcasts" value="24" icon={Megaphone} />
        <StatCard title="Avg Reach" value="1.2k" icon={Users} />
      </div>

      <Card title="New Broadcast" icon={Send} className="mb-6">
        <div className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">Message</label>
            <textarea
              rows={5}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your announcement here..."
              className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none resize-none"
            />
            <p className="text-dark-500 text-xs mt-1">{message.length}/4096 characters</p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">Pin Message</p>
                <p className="text-dark-400 text-xs">Pin this broadcast in the group</p>
              </div>
              <Toggle checked={pinMessage} onChange={setPinMessage} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">Silent Send</p>
                <p className="text-dark-400 text-xs">Send without notification sound</p>
              </div>
              <Toggle checked={silentSend} onChange={setSilentSend} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm font-medium">Schedule</p>
                <p className="text-dark-400 text-xs">Send at a specific time</p>
              </div>
              <Toggle checked={scheduleEnabled} onChange={setScheduleEnabled} />
            </div>
          </div>

          {scheduleEnabled && (
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Scheduled Time</label>
              <input
                type="datetime-local"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:border-primary-500 outline-none"
              />
            </div>
          )}

          <button
            onClick={handleBroadcast}
            disabled={sending || !message.trim()}
            className="w-full py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {sending ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                {scheduleEnabled ? <Clock className="w-5 h-5" /> : <Send className="w-5 h-5" />}
                {scheduleEnabled ? 'Schedule Broadcast' : 'Send Now'}
              </>
            )}
          </button>
        </div>
      </Card>

      <Card title="Broadcast History" icon={Megaphone}>
        <div className="space-y-3 mt-4">
          {mockHistory.map((item) => (
            <div key={item.id} className="bg-dark-800 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <p className="text-white text-sm flex-1 line-clamp-2">{item.message}</p>
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
              </div>
              <div className="flex items-center gap-4 text-dark-400 text-xs">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.sentAt}
                </span>
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {item.recipients.toLocaleString()} recipients
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
