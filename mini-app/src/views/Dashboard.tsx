import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield, Users, Settings, BarChart3, Plus, Zap,
  MessageSquare, Gamepad2, Sparkles, ChevronRight,
  Bell, Lock, Activity, Star, Crown
} from 'lucide-react'
import { useGroupStore } from '../stores/groupStore'
import { useAuthStore } from '../stores/authStore'
import { listGroups } from '../api/groups'
import Card from '../components/UI/Card'
import Loading from '../components/UI/Loading'
import ModuleToggleManager from '../components/Modules/ModuleToggleManager'
import GroupsManager from '../components/Groups/GroupsManager'
import QuickActionsPanel from '../components/Moderation/QuickActionsPanel'
import toast from 'react-hot-toast'

type ViewMode = 'groups' | 'manage' | 'quick-actions'

export default function Dashboard() {
  const navigate = useNavigate()
  const { groups, setGroups, isLoading, setLoading } = useGroupStore()
  const { user, isAuthenticated, isAuthReady, hasStoredToken } = useAuthStore()
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('groups')
  const hasLoadedGroups = useRef(false)

  useEffect(() => {
    const loadGroups = async () => {
      // Wait for auth to be fully ready (rehydrated + not loading)
      if (!isAuthReady()) {
        console.log('Skipping group load - auth not ready')
        return
      }
      
      // Check if we have a stored token that indicates user was previously authenticated
      const wasAuthenticated = hasStoredToken()
      
      if (!isAuthenticated && !wasAuthenticated) {
        console.log('Skipping group load - not authenticated and no stored token')
        return
      }
      
      // Prevent double-loading
      if (hasLoadedGroups.current) {
        console.log('Skipping group load - already loaded')
        return
      }
      
      console.log('Loading groups...', { isAuthenticated, wasAuthenticated })
      hasLoadedGroups.current = true
      setLoading(true)
      try {
        const data = await listGroups()
        setGroups(data)
      } catch (error) {
        console.error('Failed to load groups:', error)
        toast.error('Failed to load groups')
        hasLoadedGroups.current = false // Allow retry on error
      } finally {
        setLoading(false)
      }
    }

    loadGroups()
  }, [isAuthenticated, isAuthReady])

  const handleSelectGroup = (groupId: number) => {
    setSelectedGroupId(groupId)
    setViewMode('manage')
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="animate-fade-in space-y-4 sm:space-y-6">
      {/* Header - Responsive layout */}
      <div className="flex flex-col gap-3 sm:gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white truncate">
              {viewMode === 'groups' ? 'Nexus Dashboard' : 
               viewMode === 'manage' ? 'Manage Modules' : 'Quick Actions'}
            </h1>
            <p className="text-dark-400 mt-1 text-sm sm:text-base">
              {viewMode === 'groups' ? 'Manage all your Telegram groups in one place' :
               viewMode === 'manage' ? 'Toggle features on and off without commands' :
               'Execute moderation actions instantly'}
            </p>
          </div>
          
          <button
            onClick={() => {
              window.open(`https://t.me/nexusbot?startgroup=true`, '_blank')
            }}
            className="btn-primary whitespace-nowrap flex-shrink-0 self-start sm:self-auto"
          >
            <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="hidden sm:inline">Add to Group</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>

        {/* View Mode Tabs - Horizontal scroll on mobile */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-3 px-3 sm:mx-0 sm:px-0 hide-scrollbar-mobile">
          <button
            onClick={() => setViewMode('groups')}
            className={`px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors touch-target ${
              viewMode === 'groups' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white'
            }`}
          >
            <Users className="w-4 h-4" />
            <span className="text-sm sm:text-base">My Groups</span>
          </button>
          <button
            onClick={() => setViewMode('manage')}
            disabled={!selectedGroupId}
            className={`px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors touch-target ${
              viewMode === 'manage' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span className="text-sm sm:text-base">Manage</span>
          </button>
          <button
            onClick={() => setViewMode('quick-actions')}
            disabled={!selectedGroupId}
            className={`px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors touch-target ${
              viewMode === 'quick-actions' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span className="text-sm sm:text-base">Quick Actions</span>
          </button>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'groups' && (
        <GroupsManager
          onSelectGroup={handleSelectGroup}
          selectedGroupId={selectedGroupId ?? undefined}
        />
      )}

      {viewMode === 'manage' && selectedGroupId && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4 sm:space-y-6"
        >
          {/* Quick Stats - Responsive grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <QuickStatCard
              icon={<Shield className="w-4 h-4 sm:w-5 sm:h-5" />}
              label="Moderation"
              color="text-red-500"
              bgColor="bg-red-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/moderation`)}
            />
            <QuickStatCard
              icon={<Lock className="w-4 h-4 sm:w-5 sm:h-5" />}
              label="Locks"
              color="text-orange-500"
              bgColor="bg-orange-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/locks`)}
            />
            <QuickStatCard
              icon={<Bell className="w-4 h-4 sm:w-5 sm:h-5" />}
              label="Welcome"
              color="text-green-500"
              bgColor="bg-green-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/rules-greetings`)}
            />
            <QuickStatCard
              icon={<Gamepad2 className="w-4 h-4 sm:w-5 sm:h-5" />}
              label="Games"
              color="text-purple-500"
              bgColor="bg-purple-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/games`)}
            />
          </div>

          {/* Module Toggle Manager */}
          <ModuleToggleManager
            groupId={selectedGroupId}
            onModuleToggle={(name, enabled) => {
              toast.success(`${name} ${enabled ? 'enabled' : 'disabled'}`)
            }}
          />
        </motion.div>
      )}

      {viewMode === 'quick-actions' && selectedGroupId && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4 sm:space-y-6"
        >
          {/* Quick Actions Panel */}
          <QuickActionsPanel
            groupId={selectedGroupId}
            onActionComplete={() => {
              toast.success('Action completed')
            }}
          />

          {/* Quick Access Cards - Responsive grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <QuickAccessCard
              title="Manage Members"
              description="View, search, and manage all group members"
              icon={<Users className="w-5 h-5" />}
              onClick={() => navigate(`/admin/${selectedGroupId}/members`)}
            />
            <QuickAccessCard
              title="View Analytics"
              description="Check group statistics and activity"
              icon={<BarChart3 className="w-5 h-5" />}
              onClick={() => navigate(`/admin/${selectedGroupId}/analytics`)}
            />
            <QuickAccessCard
              title="Notes & Filters"
              description="Manage saved notes and auto-responses"
              icon={<MessageSquare className="w-5 h-5" />}
              onClick={() => navigate(`/admin/${selectedGroupId}/notes-filters`)}
            />
            <QuickAccessCard
              title="AI Assistant"
              description="Configure AI-powered features"
              icon={<Sparkles className="w-5 h-5" />}
              onClick={() => navigate(`/admin/${selectedGroupId}/advanced`)}
            />
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {groups.length === 0 && viewMode === 'groups' && (
        <div className="text-center py-8 sm:py-12 px-4">
          <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 bg-dark-800 rounded-full flex items-center justify-center">
            <Shield className="w-6 h-6 sm:w-8 sm:h-8 text-dark-500" />
          </div>
          <h3 className="text-base sm:text-lg font-medium text-white mb-2">No groups yet</h3>
          <p className="text-dark-400 max-w-sm mx-auto mb-4 sm:mb-6 text-sm sm:text-base">
            Add the Nexus bot to your Telegram group to get started with advanced management features.
          </p>
          <button
            onClick={() => {
              window.open(`https://t.me/nexusbot?startgroup=true`, '_blank')
            }}
            className="btn-primary"
          >
            Add Nexus to Group
          </button>
        </div>
      )}
    </div>
  )
}

// Quick Stat Card Component - Touch-friendly
function QuickStatCard({
  icon,
  label,
  color,
  bgColor,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  color: string
  bgColor: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="p-3 sm:p-4 bg-dark-800 rounded-xl border border-dark-700 hover:border-dark-600 transition-all group touch-target text-left"
    >
      <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg ${bgColor} flex items-center justify-center ${color} mb-2 sm:mb-3`}>
        {icon}
      </div>
      <p className="text-xs sm:text-sm font-medium text-white">{label}</p>
    </button>
  )
}

// Quick Access Card Component - Responsive
function QuickAccessCard({
  title,
  description,
  icon,
  onClick,
}: {
  title: string
  description: string
  icon: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="p-3 sm:p-4 bg-dark-800 rounded-xl border border-dark-700 hover:border-dark-600 transition-all text-left group touch-target"
    >
      <div className="flex items-start justify-between">
        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary-600/20 text-primary-500 flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
        <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5 text-dark-500 group-hover:text-white transition-colors flex-shrink-0" />
      </div>
      <h3 className="font-medium text-white mt-2 sm:mt-3 text-sm sm:text-base">{title}</h3>
      <p className="text-xs sm:text-sm text-dark-400 mt-1 line-clamp-2">{description}</p>
    </button>
  )
}
