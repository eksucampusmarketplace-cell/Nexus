import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { TrendingUp, Users, MessageCircle, Shield, Activity } from 'lucide-react'
import { getGroupStats } from '../../api/groups'
import StatCard from '../../components/UI/StatCard'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

export default function Analytics() {
  const { groupId } = useParams<{ groupId: string }>()
  const [stats, setStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      if (!groupId) return
      setIsLoading(true)
      try {
        const data = await getGroupStats(parseInt(groupId))
        setStats(data)
      } catch (error) {
        toast.error('Failed to load analytics')
      } finally {
        setIsLoading(false)
      }
    }

    loadStats()
  }, [groupId])

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="animate-fade-in space-y-4 sm:space-y-6">
      {/* Header - Responsive */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-white">Analytics</h1>
        <p className="text-dark-400 mt-1 text-sm sm:text-base">
          Insights and statistics for your group
        </p>
      </div>

      {/* Overview Stats - Responsive grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Total Members"
          value={stats?.total_members.toLocaleString() || '0'}
          icon={Users}
          trend="12%"
          trendUp={true}
        />
        <StatCard
          title="Active (24h)"
          value={stats?.active_members_24h.toLocaleString() || '0'}
          icon={Activity}
          trend="8%"
          trendUp={true}
        />
        <StatCard
          title="Messages (24h)"
          value={stats?.messages_24h.toLocaleString() || '0'}
          icon={MessageCircle}
          trend="5%"
          trendUp={false}
        />
        <StatCard
          title="Mood Score"
          value={`${Math.round(stats?.mood_score || 0)}%`}
          icon={TrendingUp}
        />
      </div>

      {/* Top Members */}
      <Card title="Top Members" icon={Users}>
        <div className="space-y-2 sm:space-y-3 mt-3 sm:mt-4">
          {stats?.top_members?.slice(0, 5).map((member: any, index: number) => (
            <div key={member.id} className="flex items-center gap-2 sm:gap-3 p-2 sm:p-0 -mx-2 px-2 sm:mx-0 sm:px-0 hover:bg-dark-800 sm:hover:bg-transparent rounded-lg sm:rounded-none transition-colors">
              <span className="w-5 sm:w-6 text-center text-dark-500 font-mono text-xs sm:text-sm flex-shrink-0">#{index + 1}</span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-white flex-shrink-0">
                {member.first_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm sm:text-base font-medium text-white truncate">{member.first_name}</p>
                {member.username && (
                  <p className="text-xs text-dark-400">@{member.username}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm sm:text-base font-medium text-white">{member.message_count}</p>
                <p className="text-xs text-dark-400">messages</p>
              </div>
            </div>
          ))}

          {!stats?.top_members?.length && (
            <p className="text-center text-dark-400 py-4 text-sm sm:text-base">No activity yet</p>
          )}
        </div>
      </Card>

      {/* Mod Actions */}
      <Card title="Moderation Activity" icon={Shield}>
        <div className="grid grid-cols-3 gap-2 sm:gap-4 mt-3 sm:mt-4">
          <div className="text-center p-2 sm:p-4 bg-dark-800 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-white">0</p>
            <p className="text-xs sm:text-xs text-dark-400">Warnings</p>
            <p className="text-xxs text-dark-500 hidden sm:block">(24h)</p>
          </div>
          <div className="text-center p-2 sm:p-4 bg-dark-800 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-white">0</p>
            <p className="text-xs sm:text-xs text-dark-400">Mutes</p>
            <p className="text-xxs text-dark-500 hidden sm:block">(24h)</p>
          </div>
          <div className="text-center p-2 sm:p-4 bg-dark-800 rounded-lg">
            <p className="text-lg sm:text-2xl font-bold text-white">0</p>
            <p className="text-xs sm:text-xs text-dark-400">Bans</p>
            <p className="text-xxs text-dark-500 hidden sm:block">(24h)</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
