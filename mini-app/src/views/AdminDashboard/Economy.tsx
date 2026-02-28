import { useParams } from 'react-router-dom'
import { Wallet, TrendingUp, Gift, ArrowRightLeft, Trophy } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'

const mockLeaderboard = [
  { id: 1, name: 'Alice', balance: 15420, earned: 20000 },
  { id: 2, name: 'Bob', balance: 12350, earned: 15000 },
  { id: 3, name: 'Charlie', balance: 10800, earned: 12000 },
  { id: 4, name: 'David', balance: 9200, earned: 11000 },
  { id: 5, name: 'Eve', balance: 8750, earned: 10000 },
]

export default function Economy() {
  const { groupId } = useParams<{ groupId: string }>()

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Economy</h1>
        <p className="text-dark-400 mt-1">
          Virtual currency and rewards system
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard
          title="Total Supply"
          value="45.2K"
          icon={Wallet}
        />
        <StatCard
          title="Transactions"
          value="1.2K"
          icon={ArrowRightLeft}
        />
      </div>

      {/* Currency Settings */}
      <Card title="Currency Settings" icon={Gift} className="mb-6">
        <div className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <span className="text-dark-300">Currency Name</span>
            <span className="font-medium text-white">Coins 🪙</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-dark-300">Earn per Message</span>
            <span className="font-medium text-white">1 coin</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-dark-300">Daily Bonus</span>
            <span className="font-medium text-white">100 coins</span>
          </div>
        </div>
      </Card>

      {/* Leaderboard */}
      <Card title="Leaderboard" icon={Trophy}>
        <div className="space-y-3 mt-4">
          {mockLeaderboard.map((user, index) => (
            <div key={user.id} className="flex items-center gap-3">
              <span className={`
                w-6 text-center font-bold
                ${index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-300' : index === 2 ? 'text-orange-400' : 'text-dark-500'}
              `}>
                #{index + 1}
              </span>
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                {user.name.charAt(0)}
              </div>
              <div className="flex-1">
                <span className="text-white">{user.name}</span>
              </div>
              <div className="text-right">
                <span className="font-semibold text-white">{user.balance.toLocaleString()}</span>
                <span className="text-dark-400 text-sm ml-1">🪙</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
