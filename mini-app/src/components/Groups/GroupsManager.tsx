import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Users, Settings, Shield, Bell, BarChart3, ChevronRight,
  Plus, Search, MoreVertical, Check, X, Crown, Star, Zap,
  MessageSquare, Clock, Activity
} from 'lucide-react'
import api from '../api/client'
import toast from 'react-hot-toast'

interface ManagedGroup {
  id: number
  telegramId: number
  title: string
  username?: string
  memberCount: number
  isPremium: boolean
  role: 'owner' | 'admin' | 'mod'
  enabledModulesCount: number
  lastActivity: string
  hasCustomBot: boolean
  customBotUsername?: string
  avatar?: string
}

interface GroupsManagerProps {
  onSelectGroup?: (groupId: number) => void
  selectedGroupId?: number
}

export default function GroupsManager({ onSelectGroup, selectedGroupId }: GroupsManagerProps) {
  const [groups, setGroups] = useState<ManagedGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterRole, setFilterRole] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'name' | 'members' | 'activity'>('activity')

  useEffect(() => {
    loadGroups()
  }, [])

  const loadGroups = async () => {
    try {
      setLoading(true)
      const response = await api.get('/groups/my-groups')
      setGroups(response.data)
    } catch (error) {
      console.error('Failed to load groups:', error)
      toast.error('Failed to load groups')
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort groups
  const filteredGroups = groups
    .filter(g => {
      if (filterRole && g.role !== filterRole) return false
      return g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        g.username?.toLowerCase().includes(searchQuery.toLowerCase())
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.title.localeCompare(b.title)
        case 'members':
          return b.memberCount - a.memberCount
        case 'activity':
        default:
          return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime()
      }
    })

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />
      case 'admin':
        return <Shield className="w-4 h-4 text-blue-500" />
      case 'mod':
        return <Star className="w-4 h-4 text-purple-500" />
      default:
        return null
    }
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'owner':
        return 'Owner'
      case 'admin':
        return 'Admin'
      case 'mod':
        return 'Moderator'
      default:
        return 'Member'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">My Groups</h2>
          <p className="text-dark-400">{groups.length} groups under management</p>
        </div>
        <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Add Nexus to Group
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search groups..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={filterRole || ''}
            onChange={(e) => setFilterRole(e.target.value || null)}
            className="px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:border-primary-500 outline-none"
          >
            <option value="">All Roles</option>
            <option value="owner">Owner</option>
            <option value="admin">Admin</option>
            <option value="mod">Moderator</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:border-primary-500 outline-none"
          >
            <option value="activity">Sort by Activity</option>
            <option value="name">Sort by Name</option>
            <option value="members">Sort by Members</option>
          </select>
        </div>
      </div>

      {/* Groups Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredGroups.map(group => (
          <GroupCard
            key={group.id}
            group={group}
            isSelected={selectedGroupId === group.id}
            onSelect={() => onSelectGroup?.(group.id)}
            getRoleIcon={getRoleIcon}
            getRoleLabel={getRoleLabel}
          />
        ))}
      </div>

      {filteredGroups.length === 0 && (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-dark-600 mx-auto mb-4" />
          <p className="text-dark-400">
            {searchQuery || filterRole ? 'No groups match your filters' : 'No groups found'}
          </p>
        </div>
      )}
    </div>
  )
}

// Group Card Component
function GroupCard({
  group,
  isSelected,
  onSelect,
  getRoleIcon,
  getRoleLabel,
}: {
  group: ManagedGroup
  isSelected: boolean
  onSelect: () => void
  getRoleIcon: (role: string) => React.ReactNode
  getRoleLabel: (role: string) => string
}) {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`bg-dark-800 rounded-xl border overflow-hidden transition-all cursor-pointer ${
        isSelected ? 'border-primary-500 ring-1 ring-primary-500' : 'border-dark-700 hover:border-dark-600'
      }`}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Avatar */}
            <div className="w-12 h-12 bg-dark-700 rounded-xl flex items-center justify-center text-white font-bold text-lg">
              {group.title.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-white truncate max-w-[150px]">{group.title}</h3>
                {group.isPremium && (
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                )}
              </div>
              {group.username && (
                <p className="text-sm text-dark-400">@{group.username}</p>
              )}
            </div>
          </div>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
              className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            >
              <MoreVertical className="w-5 h-5 text-dark-400" />
            </button>

            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute right-0 top-full mt-1 w-48 bg-dark-800 border border-dark-700 rounded-lg shadow-xl z-10"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button className="w-full px-4 py-3 text-left text-sm text-dark-300 hover:bg-dark-700 flex items-center gap-3">
                    <Settings className="w-4 h-4" />
                    Settings
                  </button>
                  <button className="w-full px-4 py-3 text-left text-sm text-dark-300 hover:bg-dark-700 flex items-center gap-3">
                    <BarChart3 className="w-4 h-4" />
                    Analytics
                  </button>
                  <button className="w-full px-4 py-3 text-left text-sm text-dark-300 hover:bg-dark-700 flex items-center gap-3">
                    <Bell className="w-4 h-4" />
                    Notifications
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="p-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <div className="flex items-center gap-1 text-dark-400 text-xs mb-1">
              <Users className="w-3 h-3" />
              Members
            </div>
            <p className="text-white font-semibold">{group.memberCount.toLocaleString()}</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-dark-400 text-xs mb-1">
              <Zap className="w-3 h-3" />
              Modules
            </div>
            <p className="text-white font-semibold">{group.enabledModulesCount}</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-dark-400 text-xs mb-1">
              <Activity className="w-3 h-3" />
              Activity
            </div>
            <p className="text-white font-semibold text-sm">
              {formatActivity(group.lastActivity)}
            </p>
          </div>
        </div>

        {/* Role Badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getRoleIcon(group.role)}
            <span className={`text-sm ${
              group.role === 'owner' ? 'text-yellow-400' :
              group.role === 'admin' ? 'text-blue-400' :
              'text-purple-400'
            }`}>
              {getRoleLabel(group.role)}
            </span>
          </div>

          {group.hasCustomBot && (
            <div className="flex items-center gap-1 px-2 py-1 bg-dark-700 rounded text-xs text-dark-400">
              <MessageSquare className="w-3 h-3" />
              @{group.customBotUsername}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-4 pb-4">
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              // Navigate to modules
            }}
            className="flex-1 px-3 py-2 bg-dark-700 text-dark-300 rounded-lg text-sm hover:bg-dark-600 transition-colors flex items-center justify-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Modules
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              // Navigate to dashboard
            }}
            className="flex-1 px-3 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
          >
            <ChevronRight className="w-4 h-4" />
            Manage
          </button>
        </div>
      </div>
    </motion.div>
  )
}

function formatActivity(date: string): string {
  const now = new Date()
  const last = new Date(date)
  const diffMs = now.getTime() - last.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Now'
  if (diffMins < 60) return `${diffMins}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`
  return last.toLocaleDateString()
}
