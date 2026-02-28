import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Trophy,
  Star,
  Zap,
  Target,
  TrendingUp,
  Award,
  Crown,
  Medal,
  Sparkles,
  Users,
  Settings,
  ChevronRight,
  Gift,
  ThumbsUp,
  MessageCircle,
  Flame,
  Activity,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as gamificationAPI from '../../api/gamification'

Modal.setAppElement('#root')

type TabType = 'overview' | 'leaderboard' | 'badges' | 'achievements' | 'reputation' | 'settings'

export default function GamificationHub() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [memberData, setMemberData] = useState<gamificationAPI.MemberGamification | null>(null)
  const [leaderboard, setLeaderboard] = useState<gamificationAPI.LeaderboardEntry[]>([])
  const [badges, setBadges] = useState<gamificationAPI.Badge[]>([])
  const [achievements, setAchievements] = useState<gamificationAPI.Achievement[]>([])
  const [reputation, setReputation] = useState<gamificationAPI.ReputationData | null>(null)
  const [reputationHistory, setReputationHistory] = useState<gamificationAPI.ReputationLog[]>([])
  const [config, setConfig] = useState<gamificationAPI.LevelConfig | null>(null)
  const [stats, setStats] = useState<any>(null)
  const [giveRepModalOpen, setGiveRepModalOpen] = useState(false)
  const [targetUserId, setTargetUserId] = useState('')
  const [repAmount, setRepAmount] = useState('1')
  const [repReason, setRepReason] = useState('')

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'overview':
          const [memberRes, statsRes] = await Promise.all([
            gamificationAPI.getMemberGamification(parseInt(groupId)),
            gamificationAPI.getGamificationStats(parseInt(groupId))
          ])
          setMemberData(memberRes)
          setStats(statsRes)
          break
        case 'leaderboard':
          const lbRes = await gamificationAPI.getLeaderboard(parseInt(groupId), 'xp', 50)
          setLeaderboard(lbRes)
          break
        case 'badges':
          const [allBadges, myBadges] = await Promise.all([
            gamificationAPI.getAllBadges(parseInt(groupId)),
            gamificationAPI.getMemberBadges(parseInt(groupId))
          ])
          setBadges(allBadges)
          break
        case 'achievements':
          const achRes = await gamificationAPI.getAchievements(parseInt(groupId))
          setAchievements(achRes)
          break
        case 'reputation':
          const [repRes, repHist] = await Promise.all([
            gamificationAPI.getReputation(parseInt(groupId)),
            gamificationAPI.getReputationHistory(parseInt(groupId))
          ])
          setReputation(repRes)
          setReputationHistory(repHist)
          break
        case 'settings':
          const configRes = await gamificationAPI.getLevelConfig(parseInt(groupId))
          setConfig(configRes)
          break
      }
    } catch (error) {
      console.error('Failed to load gamification data:', error)
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleGiveReputation = async () => {
    if (!groupId || !targetUserId || !repAmount) return
    try {
      await gamificationAPI.giveReputation(
        parseInt(groupId),
        parseInt(targetUserId),
        parseInt(repAmount),
        repReason || undefined
      )
      toast.success('Reputation given!')
      setGiveRepModalOpen(false)
      setTargetUserId('')
      setRepAmount('1')
      setRepReason('')
      loadData()
    } catch (error) {
      toast.error('Failed to give reputation')
    }
  }

  const getLevelColor = (level: number) => {
    if (level >= 50) return 'text-red-400'
    if (level >= 30) return 'text-purple-400'
    if (level >= 15) return 'text-blue-400'
    if (level >= 5) return 'text-green-400'
    return 'text-yellow-400'
  }

  const getLevelTitle = (level: number) => {
    if (level >= 50) return 'Legend'
    if (level >= 30) return 'Master'
    if (level >= 15) return 'Expert'
    if (level >= 5) return 'Regular'
    return 'Newbie'
  }

  if (loading && !memberData) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-yellow-500/20 to-orange-500/20 rounded-xl flex items-center justify-center">
            <Trophy className="w-6 h-6 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Identity & Gamification</h1>
            <p className="text-dark-400 mt-1">XP, levels, badges, and reputation</p>
          </div>
        </div>
        <button
          onClick={() => setGiveRepModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 hover:from-yellow-500/30 hover:to-orange-500/30 border border-yellow-500/30 rounded-xl text-yellow-400 transition-all"
        >
          <ThumbsUp className="w-4 h-4" />
          Give Rep
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: Activity },
          { id: 'leaderboard', label: 'Leaderboard', icon: Crown },
          { id: 'badges', label: 'Badges', icon: Medal },
          { id: 'achievements', label: 'Achievements', icon: Target },
          { id: 'reputation', label: 'Reputation', icon: ThumbsUp },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && memberData && (
        <div className="space-y-6">
          {/* Your Progress Card */}
          <Card className="bg-gradient-to-br from-yellow-500/10 via-orange-500/10 to-red-500/10 border-yellow-500/20">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
                  <span className="text-3xl font-bold text-white">{memberData.level}</span>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${getLevelColor(memberData.level)}`}>
                    Level {memberData.level}
                  </p>
                  <p className="text-dark-400">{getLevelTitle(memberData.level)}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Flame className="w-4 h-4 text-orange-400" />
                    <span className="text-orange-400 font-medium">{memberData.streak_days} day streak</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">{memberData.xp.toLocaleString()}</p>
                <p className="text-dark-400">Total XP</p>
              </div>
            </div>

            {/* XP Progress */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-dark-400">Progress to Level {memberData.level + 1}</span>
                <span className="text-yellow-400">{memberData.xp} / {memberData.next_level_xp} XP</span>
              </div>
              <div className="h-3 bg-dark-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full transition-all"
                  style={{ width: `${memberData.progress_percent}%` }}
                />
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mt-6">
              <div className="bg-dark-900/50 rounded-xl p-3 text-center">
                <MessageCircle className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-white">{memberData.message_count.toLocaleString()}</p>
                <p className="text-xs text-dark-500">Messages</p>
              </div>
              <div className="bg-dark-900/50 rounded-xl p-3 text-center">
                <Medal className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-white">{memberData.badges?.length || 0}</p>
                <p className="text-xs text-dark-500">Badges</p>
              </div>
              <div className="bg-dark-900/50 rounded-xl p-3 text-center">
                <ThumbsUp className="w-5 h-5 text-green-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-white">{reputation?.score || 0}</p>
                <p className="text-xs text-dark-500">Reputation</p>
              </div>
              <div className="bg-dark-900/50 rounded-xl p-3 text-center">
                <Sparkles className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                <p className="text-lg font-bold text-white">{stats?.total_achievements || 0}</p>
                <p className="text-xs text-dark-500">Achievements</p>
              </div>
            </div>
          </Card>

          {/* Recent Badges */}
          {memberData.badges && memberData.badges.length > 0 && (
            <Card title="Recent Badges" icon={Award}>
              <div className="flex gap-3 mt-4 overflow-x-auto pb-2">
                {memberData.badges.slice(0, 5).map(badge => (
                  <div
                    key={badge.id}
                    className="flex-shrink-0 w-20 text-center p-3 bg-dark-800/50 rounded-xl"
                  >
                    <span className="text-3xl">{badge.badge.icon}</span>
                    <p className="text-xs text-dark-300 mt-1 truncate">{badge.badge.name}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <Card title="XP Leaderboard" icon={Crown}>
          <div className="space-y-2 mt-4">
            {leaderboard.map((entry, index) => (
              <div
                key={entry.user_id}
                className={`flex items-center gap-3 p-3 rounded-xl ${
                  index < 3 ? 'bg-gradient-to-r from-yellow-500/10 to-transparent' : 'bg-dark-800/30'
                }`}
              >
                <span className="w-8 text-center font-bold">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${entry.rank}`}
                </span>
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                  {entry.first_name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">
                    {entry.username ? `@${entry.username}` : entry.first_name}
                  </p>
                  <p className="text-xs text-dark-500">Level {entry.level}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-white">{entry.xp.toLocaleString()}</p>
                  <p className="text-xs text-dark-500">XP</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Badges Tab */}
      {activeTab === 'badges' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {badges.map(badge => (
              <Card key={badge.id} className="text-center p-4">
                <span className="text-4xl">{badge.icon}</span>
                <h4 className="font-medium text-white mt-2">{badge.name}</h4>
                <p className="text-xs text-dark-400 mt-1">{badge.description}</p>
                <span className="inline-block mt-2 px-2 py-1 bg-dark-800 rounded text-xs text-dark-400">
                  {badge.category}
                </span>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <div className="space-y-3">
          {achievements.map(achievement => (
            <Card key={achievement.id} className={achievement.unlocked ? 'border-green-500/30' : ''}>
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                  achievement.unlocked ? 'bg-green-500/20' : 'bg-dark-800'
                }`}>
                  <Target className={`w-6 h-6 ${achievement.unlocked ? 'text-green-400' : 'text-dark-500'}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-white">{achievement.name}</h4>
                    {achievement.unlocked && <Sparkles className="w-4 h-4 text-yellow-400" />}
                  </div>
                  <p className="text-sm text-dark-400">{achievement.description}</p>
                  <div className="mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-dark-500">{achievement.category}</span>
                      <span className={achievement.unlocked ? 'text-green-400' : 'text-dark-400'}>
                        {achievement.progress} / {achievement.requirement}
                      </span>
                    </div>
                    <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          achievement.unlocked ? 'bg-green-500' : 'bg-primary-500'
                        }`}
                        style={{ width: `${Math.min(100, (achievement.progress / achievement.requirement) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Reputation Tab */}
      {activeTab === 'reputation' && reputation && (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4">
            <StatCard title="Your Rep" value={reputation.score} icon={ThumbsUp} />
            <StatCard title="Given Today" value={reputation.given_today} icon={Gift} />
            <StatCard title="Rank" value={`#${reputation.rank}`} icon={Trophy} />
          </div>

          <Card title="Recent Reputation" icon={Activity}>
            <div className="space-y-3 mt-4">
              {reputationHistory.length === 0 ? (
                <p className="text-dark-400 text-center py-8">No reputation history yet</p>
              ) : (
                reputationHistory.map(log => (
                  <div key={log.id} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        log.delta > 0 ? 'bg-green-500/20' : 'bg-red-500/20'
                      }`}>
                        <ThumbsUp className={`w-5 h-5 ${log.delta > 0 ? 'text-green-400' : 'text-red-400'}`} />
                      </div>
                      <div>
                        <p className="text-white font-medium">
                          {log.delta > 0 ? '+' : ''}{log.delta} from {log.from_user.first_name}
                        </p>
                        {log.reason && <p className="text-xs text-dark-400">{log.reason}</p>}
                      </div>
                    </div>
                    <span className="text-dark-500 text-sm">
                      {new Date(log.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && config && (
        <Card title="Gamification Settings" icon={Settings}>
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
              <div>
                <p className="text-white font-medium">Enable Levels</p>
                <p className="text-dark-400 text-sm">Track XP and level progression</p>
              </div>
              <button
                onClick={() => setConfig(prev => prev ? { ...prev, enabled: !prev.enabled } : null)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  config.enabled ? 'bg-green-500' : 'bg-dark-700'
                }`}
              >
                <span className={`block w-5 h-5 bg-white rounded-full transition-transform ${
                  config.enabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-dark-800/50 rounded-xl">
                <label className="block text-dark-400 text-sm mb-2">XP per Message</label>
                <input
                  type="number"
                  value={config.xp_per_message}
                  onChange={(e) => setConfig(prev => prev ? { ...prev, xp_per_message: parseInt(e.target.value) } : null)}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                />
              </div>
              <div className="p-4 bg-dark-800/50 rounded-xl">
                <label className="block text-dark-400 text-sm mb-2">XP per Reaction</label>
                <input
                  type="number"
                  value={config.xp_per_reaction}
                  onChange={(e) => setConfig(prev => prev ? { ...prev, xp_per_reaction: parseInt(e.target.value) } : null)}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                />
              </div>
            </div>

            <button
              onClick={() => {
                if (groupId && config) {
                  gamificationAPI.updateLevelConfig(parseInt(groupId), config)
                    .then(() => toast.success('Settings saved'))
                    .catch(() => toast.error('Failed to save'))
                }
              }}
              className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white font-medium transition-colors"
            >
              Save Settings
            </button>
          </div>
        </Card>
      )}

      {/* Give Reputation Modal */}
      <Modal
        isOpen={giveRepModalOpen}
        onRequestClose={() => setGiveRepModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Give Reputation</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Target User ID
              </label>
              <input
                type="number"
                value={targetUserId}
                onChange={(e) => setTargetUserId(e.target.value)}
                placeholder="Enter user ID"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Amount (+1 or -1)
              </label>
              <select
                value={repAmount}
                onChange={(e) => setRepAmount(e.target.value)}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="1">+1 (Upvote)</option>
                <option value="-1">-1 (Downvote)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Reason (optional)
              </label>
              <input
                type="text"
                value={repReason}
                onChange={(e) => setRepReason(e.target.value)}
                placeholder="Why are you giving rep?"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setGiveRepModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleGiveReputation}
              disabled={!targetUserId}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Give Reputation
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
