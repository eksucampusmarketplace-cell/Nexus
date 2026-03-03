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
    <div className="animate-fade-in space-y-4 sm:space-y-6">
      {/* Header - Responsive */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-white">Economy</h1>
        <p className="text-dark-400 mt-1 text-sm sm:text-base">
          Virtual currency and rewards system
        </p>
      </div>

      {/* Stats - Responsive grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
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
        <StatCard
          title="Active Users"
          value="328"
          icon={TrendingUp}
          trend="12%"
          trendUp={true}
        />
      </div>

      {/* Currency Settings */}
      <Card title="Currency Settings" icon={Gift}>
        <div className="space-y-3 sm:space-y-4 mt-3 sm:mt-4">
          <div className="flex items-center justify-between py-1">
            <span className="text-dark-300 text-sm sm:text-base">Currency Name</span>
            <span className="font-medium text-white text-sm sm:text-base">Coins 🪙</span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-dark-300 text-sm sm:text-base">Earn per Message</span>
            <span className="font-medium text-white text-sm sm:text-base">1 coin</span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-dark-300 text-sm sm:text-base">Daily Bonus</span>
            <span className="font-medium text-white text-sm sm:text-base">100 coins</span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-dark-300 text-sm sm:text-base">Weekly Bonus</span>
            <span className="font-medium text-white text-sm sm:text-base">500 coins</span>
          </div>
        </div>
      </Card>

      {/* Leaderboard */}
      <Card title="Leaderboard" icon={Trophy}>
        <div className="space-y-2 sm:space-y-3 mt-3 sm:mt-4">
          {mockLeaderboard.map((user, index) => (
            <div 
              key={user.id} 
              className="flex items-center gap-2 sm:gap-3 p-2 -mx-2 sm:mx-0 sm:p-0 hover:bg-dark-800 sm:hover:bg-transparent rounded-lg sm:rounded-none transition-colors"
            >
              <span className={`
                w-5 sm:w-6 text-center font-bold text-xs sm:text-sm flex-shrink-0
                ${index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-300' : index === 2 ? 'text-orange-400' : 'text-dark-500'}
              `}>
                #{index + 1}
              </span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold text-white flex-shrink-0">
                {user.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-white text-sm sm:text-base truncate block">{user.name}</span>
              </div>
              <div className="text-right flex-shrink-0">
                <span className="font-semibold text-white text-sm sm:text-base">{user.balance.toLocaleString()}</span>
                <span className="text-dark-400 text-xs sm:text-sm ml-1">🪙</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
