import { useEffect, useState } from 'react'
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
  const { user } = useAuthStore()
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('groups')

  useEffect(() => {
    const loadGroups = async () => {
      setLoading(true)
      try {
        const data = await listGroups()
        setGroups(data)
      } catch (error) {
        toast.error('Failed to load groups')
      } finally {
        setLoading(false)
      }
    }

    loadGroups()
  }, [])

  const handleSelectGroup = (groupId: number) => {
    setSelectedGroupId(groupId)
    setViewMode('manage')
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              {viewMode === 'groups' ? 'Nexus Dashboard' : 
               viewMode === 'manage' ? 'Manage Modules' : 'Quick Actions'}
            </h1>
            <p className="text-dark-400 mt-1">
              {viewMode === 'groups' ? 'Manage all your Telegram groups in one place' :
               viewMode === 'manage' ? 'Toggle features on and off without commands' :
               'Execute moderation actions instantly'}
            </p>
          </div>
          
          <button
            onClick={() => {
              window.open(`https://t.me/nexusbot?startgroup=true`, '_blank')
            }}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add to Group
          </button>
        </div>

        {/* View Mode Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setViewMode('groups')}
            className={`px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors ${
              viewMode === 'groups' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white'
            }`}
          >
            <Users className="w-4 h-4" />
            My Groups
          </button>
          <button
            onClick={() => setViewMode('manage')}
            disabled={!selectedGroupId}
            className={`px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors ${
              viewMode === 'manage' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Settings className="w-4 h-4" />
            Manage Modules
          </button>
          <button
            onClick={() => setViewMode('quick-actions')}
            disabled={!selectedGroupId}
            className={`px-4 py-2 rounded-lg whitespace-nowrap flex items-center gap-2 transition-colors ${
              viewMode === 'quick-actions' 
                ? 'bg-primary-600 text-white' 
                : 'bg-dark-800 text-dark-300 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Zap className="w-4 h-4" />
            Quick Actions
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
          className="space-y-6"
        >
          {/* Quick Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <QuickStatCard
              icon={<Shield className="w-5 h-5" />}
              label="Moderation"
              color="text-red-500"
              bgColor="bg-red-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/moderation`)}
            />
            <QuickStatCard
              icon={<Lock className="w-5 h-5" />}
              label="Locks"
              color="text-orange-500"
              bgColor="bg-orange-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/locks`)}
            />
            <QuickStatCard
              icon={<Bell className="w-5 h-5" />}
              label="Welcome"
              color="text-green-500"
              bgColor="bg-green-500/20"
              onClick={() => navigate(`/admin/${selectedGroupId}/rules-greetings`)}
            />
            <QuickStatCard
              icon={<Gamepad2 className="w-5 h-5" />}
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
          className="space-y-6"
        >
          {/* Quick Actions Panel */}
          <QuickActionsPanel
            groupId={selectedGroupId}
            onActionComplete={() => {
              toast.success('Action completed')
            }}
          />

          {/* Quick Access Cards */}
          <div className="grid sm:grid-cols-2 gap-4">
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
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-dark-800 rounded-full flex items-center justify-center">
            <Shield className="w-8 h-8 text-dark-500" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No groups yet</h3>
          <p className="text-dark-400 max-w-sm mx-auto mb-6">
            Add the Nexus bot to your Telegram group to get started with advanced management features.
          </p>
          <button
            onClick={() => {
              window.open(`https://t.me/nexusbot?startgroup=true`, '_blank')
            }}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Add Nexus to Group
          </button>
        </div>
      )}
    </div>
  )
}

// Quick Stat Card Component
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
      className="p-4 bg-dark-800 rounded-xl border border-dark-700 hover:border-dark-600 transition-all group"
    >
      <div className={`w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center ${color} mb-3`}>
        {icon}
      </div>
      <p className="text-sm font-medium text-white">{label}</p>
    </button>
  )
}

// Quick Access Card Component
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
      className="p-4 bg-dark-800 rounded-xl border border-dark-700 hover:border-dark-600 transition-all text-left group"
    >
      <div className="flex items-start justify-between">
        <div className="w-10 h-10 rounded-lg bg-primary-600/20 text-primary-500 flex items-center justify-center">
          {icon}
        </div>
        <ChevronRight className="w-5 h-5 text-dark-500 group-hover:text-white transition-colors" />
      </div>
      <h3 className="font-medium text-white mt-3">{title}</h3>
      <p className="text-sm text-dark-400 mt-1">{description}</p>
    </button>
  )
}
