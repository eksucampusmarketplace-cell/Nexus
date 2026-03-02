import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { TrendingUp, Users, MessageCircle, Shield, Activity } from 'lucide-react'
import { getGroupStats } from '../../api/groups'
import StatCard from '../../components/UI/StatCard'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import MemberActionCard from '../../components/Moderation/MemberActionCard'
import type { MemberActionTarget } from '../../components/Moderation/MemberActionCard'
import toast from 'react-hot-toast'

export default function Analytics() {
  const { groupId } = useParams<{ groupId: string }>()
  const [stats, setStats] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [actionTarget, setActionTarget] = useState<MemberActionTarget | null>(null)

  useEffect(() => {
    const loadStats = async () => {
      if (!groupId) return
      setIsLoading(true)
      try {
        const data = await getGroupStats(parseInt(groupId))
        setStats(data)
      } catch {
        toast.error('Failed to load analytics')
      } finally {
        setIsLoading(false)
      }
    }

    loadStats()
  }, [groupId])

  const openMemberAction = (member: any) => {
    if (!groupId) return
    setActionTarget({
      userId: member.user_id ?? member.id,
      groupId: parseInt(groupId),
      firstName: member.first_name,
      username: member.username ?? null,
      trustScore: member.trust_score ?? 50,
      level: member.level ?? 1,
      role: member.role ?? 'member',
      warnCount: member.warn_count ?? 0,
      isMuted: member.is_muted ?? false,
      isBanned: member.is_banned ?? false,
    })
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-dark-400 mt-1">
          Insights and statistics — tap any member to take action
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Total Members"
          value={stats?.total_members?.toLocaleString() || '0'}
          icon={Users}
          trend="12%"
          trendUp={true}
        />
        <StatCard
          title="Active (24h)"
          value={stats?.active_members_24h?.toLocaleString() || '0'}
          icon={Activity}
          trend="8%"
          trendUp={true}
        />
        <StatCard
          title="Messages (24h)"
          value={stats?.messages_24h?.toLocaleString() || '0'}
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

      {/* Top Members — each row is tappable */}
      <Card title="Top Members" icon={Users}>
        <div className="space-y-1 mt-4">
          {stats?.top_members?.slice(0, 10).map((member: any, index: number) => (
            <button
              key={member.id}
              className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-dark-800 transition-colors text-left"
              onClick={() => openMemberAction(member)}
            >
              <span className="w-6 text-center text-dark-500 font-mono text-sm">#{index + 1}</span>
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                {member.first_name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{member.first_name}</p>
                {member.username && (
                  <p className="text-xs text-dark-400">@{member.username}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-medium text-white">{member.message_count}</p>
                <p className="text-xs text-dark-400">messages</p>
              </div>
            </button>
          ))}

          {!stats?.top_members?.length && (
            <p className="text-center text-dark-400 py-4">No activity yet</p>
          )}
        </div>
      </Card>

      {/* Mod Actions */}
      <div className="mt-6">
        <Card title="Moderation Activity" icon={Shield}>
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="text-center p-4 bg-dark-800 rounded-lg">
              <p className="text-2xl font-bold text-white">{stats?.mod_actions_24h ?? 0}</p>
              <p className="text-xs text-dark-400">Actions (24h)</p>
            </div>
            <div className="text-center p-4 bg-dark-800 rounded-lg">
              <p className="text-2xl font-bold text-white">{stats?.new_members_7d ?? 0}</p>
              <p className="text-xs text-dark-400">New (7d)</p>
            </div>
            <div className="text-center p-4 bg-dark-800 rounded-lg">
              <p className="text-2xl font-bold text-white">{stats?.active_members_7d ?? 0}</p>
              <p className="text-xs text-dark-400">Active (7d)</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Member Action Card */}
      <MemberActionCard
        target={actionTarget}
        onClose={() => setActionTarget(null)}
      />
    </div>
  )
}
