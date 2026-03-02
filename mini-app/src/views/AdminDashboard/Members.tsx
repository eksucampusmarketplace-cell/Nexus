import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Search, Filter, UserX, VolumeX, Ban, Shield, UserCheck, MoreVertical } from 'lucide-react'
import { listMembers } from '../../api/members'
import type { Member } from '../../api/members'
import Loading from '../../components/UI/Loading'
import Badge from '../../components/UI/Badge'
import toast from 'react-hot-toast'

const roleColors: Record<string, { bg: string; text: string }> = {
  owner: { bg: 'bg-purple-500/20', text: 'text-purple-500' },
  admin: { bg: 'bg-blue-500/20', text: 'text-blue-500' },
  mod: { bg: 'bg-green-500/20', text: 'text-green-500' },
  trusted: { bg: 'bg-yellow-500/20', text: 'text-yellow-500' },
  member: { bg: 'bg-dark-700', text: 'text-dark-300' },
  restricted: { bg: 'bg-red-500/20', text: 'text-red-500' },
}

export default function Members() {
  const { groupId } = useParams<{ groupId: string }>()
  const [members, setMembers] = useState<Member[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('')

  useEffect(() => {
    const loadMembers = async () => {
      if (!groupId) return
      setIsLoading(true)
      try {
        const data = await listMembers(parseInt(groupId))
        setMembers(data)
      } catch (error) {
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

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="animate-fade-in space-y-4 sm:space-y-6">
      {/* Header - Responsive */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-white">Members</h1>
        <p className="text-dark-400 mt-1 text-sm sm:text-base">
          {members.length.toLocaleString()} total members
        </p>
      </div>

      {/* Search and Filter - Stack on mobile */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search members..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="select sm:w-auto"
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
            className="bg-dark-900 rounded-xl border border-dark-800 p-3 sm:p-4 hover:border-dark-700 transition-colors"
          >
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Avatar */}
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-white flex-shrink-0">
                {member.first_name.charAt(0).toUpperCase()}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                  <span className="font-medium text-white text-sm sm:text-base truncate">
                    {member.first_name} {member.last_name || ''}
                  </span>
                  {member.username && (
                    <span className="text-xs sm:text-sm text-dark-400">@{member.username}</span>
                  )}
                </div>
                <div className="flex items-center gap-1.5 sm:gap-2 mt-0.5 flex-wrap">
                  <Badge
                    variant={member.role === 'restricted' ? 'error' : 'default'}
                    size="sm"
                  >
                    {member.role}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {member.is_muted && (
                      <VolumeX className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-yellow-500" />
                    )}
                    {member.is_banned && (
                      <Ban className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-red-500" />
                    )}
                    {member.is_whitelisted && (
                      <Shield className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-green-500" />
                    )}
                  </div>
                </div>
              </div>

              {/* Stats - Hidden on mobile, shown on tablet+ */}
              <div className="hidden sm:flex items-center gap-3 lg:gap-4 text-xs sm:text-sm text-dark-400">
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

              {/* Actions */}
              <button className="p-2 hover:bg-dark-800 rounded-lg transition-colors touch-target">
                <MoreVertical className="w-4 h-4 sm:w-5 sm:h-5 text-dark-400" />
              </button>
            </div>

            {/* Mobile Stats Row */}
            <div className="flex sm:hidden items-center gap-4 mt-2 pt-2 border-t border-dark-800 text-xs text-dark-400">
              <div className="flex items-center gap-1">
                <span className="font-semibold text-white">{member.message_count}</span>
                <span>msgs</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="font-semibold text-white">Lvl {member.level}</span>
                <span>({member.xp} XP)</span>
              </div>
              <div className="flex items-center gap-1">
                <span className={`font-semibold ${member.trust_score >= 70 ? 'text-green-500' : member.trust_score >= 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                  {member.trust_score}
                </span>
                <span>trust</span>
              </div>
            </div>
          </div>
        ))}

        {filteredMembers.length === 0 && (
          <div className="text-center py-8 sm:py-12">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-dark-800 rounded-full flex items-center justify-center">
              <UserX className="w-6 h-6 sm:w-8 sm:h-8 text-dark-500" />
            </div>
            <p className="text-dark-400 text-sm sm:text-base">No members found</p>
          </div>
        )}
      </div>
    </div>
  )
}
