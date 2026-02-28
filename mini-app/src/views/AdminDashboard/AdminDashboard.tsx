import { useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Users,
  Shield,
  BarChart3,
  Settings,
  Calendar,
  Wallet,
  ChevronRight,
  MessageSquare,
  Zap,
  Bot,
  Scissors,
  Download,
  Flow,
  AlertTriangle,
  Hash,
  Lock,
  Ban,
  FileText,
  Upload,
  Key,
  Trophy,
  Heart,
  Gamepad2,
  Megaphone,
  Workflow,
  Type,
  Search,
} from 'lucide-react'
import { useGroupStore } from '../../stores/groupStore'
import { useAuthStore } from '../../stores/authStore'
import { getGroup, getGroupStats } from '../../api/groups'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

const menuItems = [
  { icon: Users, label: 'Members', path: 'members', color: 'text-blue-500' },
  { icon: AlertTriangle, label: 'Moderation', path: 'moderation', color: 'text-red-500' },
  { icon: Shield, label: 'Modules', path: 'modules', color: 'text-purple-500' },
  { icon: Hash, label: 'Notes & Filters', path: 'notes-filters', color: 'text-cyan-500' },
  { icon: Lock, label: 'Locks', path: 'locks', color: 'text-orange-500' },
  { icon: Ban, label: 'Anti-Spam', path: 'antispam', color: 'text-yellow-500' },
  { icon: FileText, label: 'Rules & Greetings', path: 'rules-greetings', color: 'text-green-500' },
  { icon: BarChart3, label: 'Analytics', path: 'analytics', color: 'text-emerald-500' },
  { icon: Calendar, label: 'Scheduler', path: 'scheduler', color: 'text-pink-500' },
  { icon: Wallet, label: 'Economy', path: 'economy', color: 'text-amber-500' },
  { icon: Upload, label: 'Import/Export', path: 'import-export', color: 'text-indigo-500' },
  { icon: Key, label: 'Custom Bot', path: 'custom-bot', color: 'text-violet-500' },
  { icon: Flow, label: 'Bot Builder', path: 'bot-builder', color: 'text-rose-500' },
  { icon: Scissors, label: 'Advanced', path: 'advanced', color: 'text-teal-500' },
  { icon: Settings, label: 'Settings', path: 'settings', color: 'text-gray-500' },
  { icon: Zap, label: 'Integrations', path: 'integrations', color: 'text-teal-500' },
  { icon: Trophy, label: 'Gamification', path: 'gamification', color: 'text-yellow-500' },
  { icon: Heart, label: 'Community', path: 'community', color: 'text-pink-500' },
  { icon: Gamepad2, label: 'Games', path: 'games', color: 'text-purple-500' },
  { icon: Megaphone, label: 'Broadcast', path: 'broadcast', color: 'text-blue-500' },
  { icon: Workflow, label: 'Automation', path: 'automation', color: 'text-indigo-500' },
  { icon: Type, label: 'Formatting', path: 'formatting', color: 'text-emerald-500' },
  { icon: Search, label: 'Search', path: 'search', color: 'text-cyan-500' },
]

export default function AdminDashboard() {
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()
  const { currentGroup, setCurrentGroup, isLoading, setLoading } = useGroupStore()
  const { user } = useAuthStore()
  
  useEffect(() => {
    const loadGroup = async () => {
      if (!groupId) return
      
      setLoading(true)
      try {
        const [group, stats] = await Promise.all([
          getGroup(parseInt(groupId)),
          getGroupStats(parseInt(groupId)),
        ])
        setCurrentGroup(group)
      } catch (error) {
        toast.error('Failed to load group')
        navigate('/')
      } finally {
        setLoading(false)
      }
    }
  
    loadGroup()
  }, [groupId])
  
  if (isLoading || !currentGroup) {
    return <Loading />
  }
  
  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center text-2xl font-bold text-white">
          {currentGroup.title.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-white">{currentGroup.title}</h1>
          <p className="text-dark-400 text-sm">
            {currentGroup.member_count.toLocaleString()} members • {currentGroup.language.toUpperCase()}
          </p>
        </div>
      </div>
  
      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Total Members"
          value={currentGroup.member_count.toLocaleString()}
          icon={Users}
          trend="12%"
          trendUp={true}
        />
        <StatCard
          title="Active Today"
          value="248"
          icon={Zap}
          trend="8%"
          trendUp={true}
        />
        <StatCard
          title="Messages"
          value="1.2k"
          icon={MessageSquare}
          trend="5%"
          trendUp={false}
        />
        <StatCard
          title="Trust Score"
          value="87%"
          icon={Shield}
          trend="Stable"
        />
      </div>
  
      {/* Quick Actions */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={`/admin/${groupId}/${item.path}`}
              className="flex items-center gap-3 p-4 bg-dark-900 rounded-xl border border-dark-800 hover:border-dark-700 hover:bg-dark-800 transition-all"
            >
              <item.icon className={`w-5 h-5 ${item.color}`} />
              <span className="font-medium text-white text-sm">{item.label}</span>
              <ChevronRight className="w-4 h-4 text-dark-500 ml-auto" />
            </Link>
          ))}
        </div>
      </div>
  
      {/* Bot Status */}
      <Card
        title="Bot Status"
        description="All systems operational"
        icon={Bot}
      >
        <div className="flex items-center gap-2 mt-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-green-500">Online</span>
        </div>
      </Card>
    </div>
  )
}
