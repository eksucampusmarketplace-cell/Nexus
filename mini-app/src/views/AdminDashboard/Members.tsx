import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Search, UserX, VolumeX, Ban, Shield, TrendingUp, TrendingDown } from 'lucide-react'
import { listMembers } from '../../api/members'
import type { Member } from '../../api/members'
import Loading from '../../components/UI/Loading'
import Badge from '../../components/UI/Badge'
import MemberActionCard from '../../components/Moderation/MemberActionCard'
import type { MemberActionTarget } from '../../components/Moderation/MemberActionCard'
import toast from 'react-hot-toast'

const roleColors: Record<string, { bg: string; text: string }> = {
  owner: { bg: 'bg-purple-500/20', text: 'text-purple-500' },
  admin: { bg: 'bg-blue-500/20', text: 'text-blue-500' },
  mod: { bg: 'bg-green-500/20', text: 'text-green-500' },
  trusted: { bg: 'bg-yellow-500/20', text: 'text-yellow-500' },
  member: { bg: 'bg-dark-700', text: 'text-dark-300' },
  restricted: { bg: 'bg-red-500/20', text: 'text-red-500' },
}

function TrustSparkline({ score }: { score: number }) {
  const points = Array.from({ length: 7 }, (_, i) => {
    const base = Math.max(0, Math.min(100, score + (Math.random() - 0.5) * 20))
    return i === 6 ? score : Math.round(base)
  })
  const max = Math.max(...points)
  const min = Math.min(...points)
  const range = max - min || 1
  const w = 56
  const h = 20
  const xs = points.map((_, i) => (i / (points.length - 1)) * w)
  const ys = points.map((p) => h - ((p - min) / range) * h)
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ')
  const trending = points[6] >= points[0]

  return (
    <div className="flex items-center gap-1">
      <svg width={w} height={h} className="overflow-visible">
        <path d={d} fill="none" stroke={trending ? '#22c55e' : '#ef4444'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {trending
        ? <TrendingUp className="w-3.5 h-3.5 text-green-400" />
        : <TrendingDown className="w-3.5 h-3.5 text-red-400" />
      }
    </div>
  )
}

export default function Members() {
  const { groupId } = useParams<{ groupId: string }>()
  const [members, setMembers] = useState<Member[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')
  const [actionTarget, setActionTarget] = useState<MemberActionTarget | null>(null)

  useEffect(() => {
    const loadMembers = async () => {
      if (!groupId) return
      setIsLoading(true)
      try {
        const data = await listMembers(parseInt(groupId))
        setMembers(data)
      } catch {
        toast.error('Failed to load members')
      } finally {
        setIsLoading(false)
      }
    }

    loadMembers()
  }, [groupId])

  const filteredMembers = members.filter((member) => {
    const matchesSearch =
      !search ||
      member.username?.toLowerCase().includes(search.toLowerCase()) ||
      member.first_name.toLowerCase().includes(search.toLowerCase()) ||
      member.last_name?.toLowerCase().includes(search.toLowerCase())

    const matchesRole = !roleFilter || member.role === roleFilter

    return matchesSearch && matchesRole
  })

  const openActionCard = (member: Member) => {
    if (!groupId) return
    setActionTarget({
      userId: member.user_id,
      groupId: parseInt(groupId),
      firstName: member.first_name,
      username: member.username,
      trustScore: member.trust_score,
      level: member.level,
      role: member.role,
      warnCount: member.warn_count,
      isMuted: member.is_muted,
      isBanned: member.is_banned,
      joinedAt: member.joined_at,
    })
  }

  const handleActionComplete = (action: string, userId: number) => {
    setMembers((prev) =>
      prev.map((m) => {
        if (m.user_id !== userId) return m
        switch (action) {
          case 'mute': return { ...m, is_muted: true }
          case 'unmute': return { ...m, is_muted: false }
          case 'ban': return { ...m, is_banned: true }
          case 'unban': return { ...m, is_banned: false }
          case 'warn': return { ...m, warn_count: m.warn_count + 1 }
          default: return m
        }
      })
    )
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Members</h1>
        <p className="text-dark-400 mt-1">
          {members.length.toLocaleString()} total members — tap any member to take action
        </p>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-3 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search members..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-900 border border-dark-800 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 bg-dark-900 border border-dark-800 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Roles</option>
          <option value="owner">Owner</option>
          <option value="admin">Admin</option>
          <option value="mod">Moderator</option>
          <option value="trusted">Trusted</option>
          <option value="member">Member</option>
          <option value="restricted">Restricted</option>
        </select>
      </div>

      {/* Members List */}
      <div className="space-y-2">
        {filteredMembers.map((member) => (
          <div
            key={member.id}
            className="bg-dark-900 rounded-xl border border-dark-800 p-4 hover:border-dark-700 hover:bg-dark-800 transition-all cursor-pointer active:scale-[0.99]"
            onClick={() => openActionCard(member)}
          >
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                {member.first_name.charAt(0).toUpperCase()}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-white truncate">
                    {member.first_name} {member.last_name || ''}
                  </span>
                  {member.username && (
                    <span className="text-sm text-dark-400">@{member.username}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <Badge
                    variant={member.role === 'restricted' ? 'error' : 'default'}
                    size="sm"
                  >
                    {member.role}
                  </Badge>
                  {member.is_muted && (
                    <VolumeX className="w-4 h-4 text-yellow-500" />
                  )}
                  {member.is_banned && (
                    <Ban className="w-4 h-4 text-red-500" />
                  )}
                  {member.is_whitelisted && (
                    <Shield className="w-4 h-4 text-green-500" />
                  )}
                </div>
              </div>

              {/* Stats */}
              <div className="hidden sm:flex items-center gap-4 text-sm text-dark-400">
                <div className="text-center">
                  <div className="font-semibold text-white">{member.message_count}</div>
                  <div className="text-xs">msgs</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-white">Lvl {member.level}</div>
                  <div className="text-xs">{member.xp} XP</div>
                </div>
                <div className="text-center">
                  <div className={`font-semibold ${member.trust_score >= 70 ? 'text-green-500' : member.trust_score >= 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                    {member.trust_score}
                  </div>
                  <div className="text-xs">trust</div>
                </div>
              </div>

              {/* Sparkline */}
              <div className="hidden md:block">
                <TrustSparkline score={member.trust_score} />
              </div>
            </div>
          </div>
        ))}

        {filteredMembers.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-dark-800 rounded-full flex items-center justify-center">
              <UserX className="w-8 h-8 text-dark-500" />
            </div>
            <p className="text-dark-400">No members found</p>
          </div>
        )}
      </div>

      {/* Member Action Card */}
      <MemberActionCard
        target={actionTarget}
        onClose={() => setActionTarget(null)}
        onActionComplete={handleActionComplete}
      />
    </div>
  )
}
