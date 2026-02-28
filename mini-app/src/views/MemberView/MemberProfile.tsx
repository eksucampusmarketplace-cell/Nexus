import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  User,
  Trophy,
  Star,
  Shield,
  MessageCircle,
  TrendingUp,
  Award,
  Wallet,
} from 'lucide-react'
import { getGroup } from '../../api/groups'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

const mockBadges = [
  { id: 1, name: 'Early Adopter', icon: '🚀', color: 'bg-blue-500' },
  { id: 2, name: 'Active Member', icon: '🔥', color: 'bg-orange-500' },
  { id: 3, name: 'Helper', icon: '💪', color: 'bg-green-500' },
  { id: 4, name: 'VIP', icon: '👑', color: 'bg-yellow-500' },
]

export default function MemberProfile() {
  const { groupId } = useParams<{ groupId: string }>()
  const [group, setGroup] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadGroup = async () => {
      if (!groupId) return
      setIsLoading(true)
      try {
        const data = await getGroup(parseInt(groupId))
        setGroup(data)
      } catch (error) {
        toast.error('Failed to load group')
      } finally {
        setIsLoading(false)
      }
    }

    loadGroup()
  }, [groupId])

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Profile Header */}
      <div className="text-center mb-6">
        <div className="w-24 h-24 mx-auto bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-3xl font-bold text-white mb-4">
          You
        </div>
        <h1 className="text-xl font-bold text-white">Your Profile</h1>
        <p className="text-dark-400">{group?.title}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Level"
          value="12"
          icon={Trophy}
        />
        <StatCard
          title="XP"
          value="1,240"
          icon={Star}
        />
        <StatCard
          title="Messages"
          value="456"
          icon={MessageCircle}
        />
        <StatCard
          title="Trust"
          value="85%"
          icon={Shield}
        />
      </div>

      {/* XP Progress */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-300">Level 12 Progress</span>
          <span className="text-sm text-dark-400">240/500 XP</span>
        </div>
        <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full" style={{ width: '48%' }} />
        </div>
        <p className="text-xs text-dark-500 mt-2">260 XP to next level</p>
      </Card>

      {/* Badges */}
      <Card title="Badges" icon={Award} className="mb-6">
        <div className="grid grid-cols-4 gap-3 mt-4">
          {mockBadges.map((badge) => (
            <div key={badge.id} className="text-center">
              <div className={`w-12 h-12 mx-auto ${badge.color} rounded-xl flex items-center justify-center text-2xl mb-2`}>
                {badge.icon}
              </div>
              <p className="text-xs text-dark-300">{badge.name}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Wallet */}
      <Card title="Wallet" icon={Wallet}>
        <div className="flex items-center justify-between p-4 bg-dark-800 rounded-lg mt-4">
          <div>
            <p className="text-sm text-dark-400">Balance</p>
            <p className="text-2xl font-bold text-white">1,250 🪙</p>
          </div>
          <button className="btn-primary text-sm">
            Daily Claim
          </button>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card title="Recent Activity" icon={TrendingUp} className="mt-6">
        <div className="space-y-3 mt-4">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-green-500">+10 XP</span>
            <span className="text-dark-300">Sent a message</span>
            <span className="text-dark-500 ml-auto">2m ago</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-green-500">+5 🪙</span>
            <span className="text-dark-300">Daily bonus</span>
            <span className="text-dark-500 ml-auto">1h ago</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <Badge variant="success" size="sm">Badge</Badge>
            <span className="text-dark-300">Earned "Active Member"</span>
            <span className="text-dark-500 ml-auto">2d ago</span>
          </div>
        </div>
      </Card>
    </div>
  )
}
