import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: string
  trendUp?: boolean
}

export default function StatCard({ title, value, icon: Icon, trend, trendUp }: StatCardProps) {
  return (
    <div className="bg-dark-900 rounded-xl border border-dark-800 p-3 sm:p-4 hover:border-dark-700 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-dark-400 text-xs sm:text-sm truncate">{title}</p>
          <p className="text-lg sm:text-2xl font-bold text-white mt-0.5 sm:mt-1 truncate">{value}</p>
          {trend && (
            <p className={`text-xs mt-0.5 sm:mt-1 ${trendUp ? 'text-green-500' : trendUp === false ? 'text-red-500' : 'text-dark-400'}`}>
              {trendUp === true ? '↑' : trendUp === false ? '↓' : '•'} {trend}
            </p>
          )}
        </div>
        <div className="p-2 sm:p-3 bg-primary-500/10 rounded-lg flex-shrink-0">
          <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
        </div>
      </div>
    </div>
  )
}
