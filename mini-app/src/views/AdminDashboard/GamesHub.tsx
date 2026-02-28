import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Gamepad2,
  Trophy,
  Target,
  Zap,
  Users,
  Settings,
  Play,
  Crown,
  Medal,
  Star,
  Flame,
  Dice5,
  Brain,
  Puzzle,
  Swords,
  ChevronRight,
  Clock,
  TrendingUp,
  Gift,
  Lock,
  Unlock,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as gamesAPI from '../../api/games'

Modal.setAppElement('#root')

type TabType = 'games' | 'leaderboard' | 'rewards' | 'active' | 'settings'

const GAME_ICONS: Record<string, any> = {
  trivia: Brain,
  hangman: Puzzle,
  rps: Swords,
  dice: Dice5,
  trivia_quiz: Brain,
  word_scramble: Puzzle,
  number_guess: Target,
  chess: Crown,
}

const GAME_COLORS: Record<string, string> = {
  trivia: 'from-blue-500/20 to-cyan-500/20',
  hangman: 'from-purple-500/20 to-pink-500/20',
  rps: 'from-red-500/20 to-orange-500/20',
  dice: 'from-green-500/20 to-emerald-500/20',
  trivia_quiz: 'from-blue-500/20 to-indigo-500/20',
  word_scramble: 'from-purple-500/20 to-violet-500/20',
  number_guess: 'from-yellow-500/20 to-amber-500/20',
  chess: 'from-gray-500/20 to-slate-500/20',
}

export default function GamesHub() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('games')
  const [config, setConfig] = useState<gamesAPI.GameConfig | null>(null)
  const [leaderboards, setLeaderboards] = useState<gamesAPI.GameLeaderboard[]>([])
  const [rewards, setRewards] = useState<gamesAPI.GameReward[]>([])
  const [activeGames, setActiveGames] = useState<gamesAPI.ActiveGame[]>([])
  const [stats, setStats] = useState<gamesAPI.GameStats | null>(null)
  const [availableGames, setAvailableGames] = useState<string[]>([])
  
  // Modal states
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [gameHistoryModalOpen, setGameHistoryModalOpen] = useState(false)
  const [selectedGame, setSelectedGame] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'games':
          const [gamesRes, availGames] = await Promise.all([
            gamesAPI.getGameConfig(parseInt(groupId)),
            gamesAPI.getAvailableGames(parseInt(groupId))
          ])
          setConfig(gamesRes)
          setAvailableGames(availGames)
          break
        case 'leaderboard':
          const lbRes = await gamesAPI.getGameLeaderboard(parseInt(groupId))
          setLeaderboards(lbRes)
          break
        case 'rewards':
          const rewardsRes = await gamesAPI.getGameRewards(parseInt(groupId))
          setRewards(rewardsRes)
          break
        case 'active':
          const [activeRes, statsRes] = await Promise.all([
            gamesAPI.getActiveGames(parseInt(groupId)),
            gamesAPI.getGameStats(parseInt(groupId))
          ])
          setActiveGames(activeRes)
          setStats(statsRes)
          break
        case 'settings':
          const configRes = await gamesAPI.getGameConfig(parseInt(groupId))
          setConfig(configRes)
          break
      }
    } catch (error) {
      console.error('Failed to load games data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleGame = (gameType: string) => {
    if (!config) return
    const enabled = config.enabled_games.includes(gameType)
    const newEnabled = enabled
      ? config.enabled_games.filter(g => g !== gameType)
      : [...config.enabled_games, gameType]
    setConfig({ ...config, enabled_games: newEnabled })
  }

  const saveSettings = async () => {
    if (!groupId || !config) return
    try {
      await gamesAPI.updateGameConfig(parseInt(groupId), config)
      toast.success('Settings saved!')
      setSettingsModalOpen(false)
    } catch (error) {
      toast.error('Failed to save settings')
    }
  }

  const claimReward = async (rewardId: number) => {
    if (!groupId) return
    try {
      await gamesAPI.claimGameReward(parseInt(groupId), rewardId)
      toast.success('Reward claimed!')
      loadData()
    } catch (error) {
      toast.error('Failed to claim reward')
    }
  }

  const getGameIcon = (gameType: string) => {
    return GAME_ICONS[gameType] || Gamepad2
  }

  const getGameColor = (gameType: string) => {
    return GAME_COLORS[gameType] || 'from-primary-500/20 to-accent-500/20'
  }

  const getGameName = (gameType: string) => {
    return gameType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  if (loading && !config) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-purple-500/20 rounded-xl flex items-center justify-center">
            <Gamepad2 className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Games Hub</h1>
            <p className="text-dark-400 mt-1">Configure games, view leaderboards, manage rewards</p>
          </div>
        </div>
        <button
          onClick={() => setSettingsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'games', label: 'Games', icon: Gamepad2 },
          { id: 'leaderboard', label: 'Leaderboards', icon: Trophy },
          { id: 'rewards', label: 'Rewards', icon: Gift },
          { id: 'active', label: 'Active Games', icon: Play },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Games Tab */}
      {activeTab === 'games' && (
        <div className="space-y-6">
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard title="Total Plays" value={stats.total_plays} icon={Play} />
              <StatCard title="Unique Players" value={stats.unique_players} icon={Users} />
              <StatCard title="Active Games" value={config?.enabled_games.length || 0} icon={Gamepad2} />
              <StatCard title="Most Played" value={getGameName(stats.most_played)} icon={TrendingUp} />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableGames.map(gameType => {
              const isEnabled = config?.enabled_games.includes(gameType)
              const Icon = getGameIcon(gameType)
              
              return (
                <Card
                  key={gameType}
                  className={`cursor-pointer transition-all ${isEnabled ? '' : 'opacity-60'}`}
                  onClick={() => toggleGame(gameType)}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${getGameColor(gameType)} flex items-center justify-center`}>
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-white">{getGameName(gameType)}</h3>
                        {isEnabled ? (
                          <span className="px-2 py-0.5 bg-green-500/20 rounded text-xs text-green-400">Active</span>
                        ) : (
                          <span className="px-2 py-0.5 bg-dark-700 rounded text-xs text-dark-400">Disabled</span>
                        )}
                      </div>
                      <p className="text-sm text-dark-400 mt-1">
                        {isEnabled ? 'Click to disable' : 'Click to enable'}
                      </p>
                    </div>
                    <div className={`w-10 h-6 rounded-full transition-colors ${
                      isEnabled ? 'bg-green-500' : 'bg-dark-700'
                    }`}>
                      <span className={`block w-5 h-5 bg-white rounded-full transition-transform mt-0.5 ${
                        isEnabled ? 'translate-x-4' : 'translate-x-0.5'
                      }`} />
                    </div>
                  </div>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="space-y-6">
          {leaderboards.map(lb => (
            <Card key={lb.game_type} title={getGameName(lb.game_type)} icon={Trophy}>
              <div className="space-y-2 mt-4">
                {lb.entries.length === 0 ? (
                  <p className="text-dark-400 text-center py-8">No scores yet</p>
                ) : (
                  lb.entries.slice(0, 10).map((entry, index) => (
                    <div
                      key={entry.user_id}
                      className={`flex items-center gap-3 p-3 rounded-xl ${
                        index < 3 ? 'bg-gradient-to-r from-yellow-500/10 to-transparent' : 'bg-dark-800/30'
                      }`}
                    >
                      <span className="w-8 text-center font-bold">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                      </span>
                      <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                        {entry.first_name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">
                          {entry.username ? `@${entry.username}` : entry.first_name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-white">{entry.score.toLocaleString()}</p>
                        <p className="text-xs text-dark-500">points</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Rewards Tab */}
      {activeTab === 'rewards' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rewards.map(reward => (
              <Card
                key={reward.id}
                className={reward.unlocked ? 'border-green-500/30' : ''}
              >
                <div className="flex items-start gap-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                    reward.unlocked
                      ? 'bg-gradient-to-br from-green-400 to-emerald-500'
                      : 'bg-dark-800'
                  }`}>
                    <span className="text-2xl">{reward.icon}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-white">{reward.name}</h3>
                      {reward.unlocked && <Star className="w-4 h-4 text-yellow-400" />}
                    </div>
                    <p className="text-sm text-dark-400">{reward.description}</p>
                    
                    <div className="mt-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-dark-500">{reward.requirement_type}</span>
                        <span className={reward.unlocked ? 'text-green-400' : 'text-dark-400'}>
                          {reward.progress} / {reward.requirement_value}
                        </span>
                      </div>
                      <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            reward.unlocked ? 'bg-green-500' : 'bg-primary-500'
                          }`}
                          style={{ width: `${Math.min(100, (reward.progress / reward.requirement_value) * 100)}%` }}
                        />
                      </div>
                    </div>

                    {reward.unlocked && !reward.unlocked_at && (
                      <button
                        onClick={() => claimReward(reward.id)}
                        className="mt-3 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-sm font-medium transition-colors"
                      >
                        Claim Reward
                      </button>
                    )}

                    {reward.unlocked && reward.unlocked_at && (
                      <p className="mt-3 text-xs text-green-400">
                        Claimed on {new Date(reward.unlocked_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Active Games Tab */}
      {activeTab === 'active' && (
        <div className="space-y-6">
          {activeGames.length === 0 ? (
            <Card>
              <div className="text-center py-12">
                <Play className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                <p className="text-dark-400">No active games</p>
                <p className="text-sm text-dark-500 mt-1">Games will appear here when members start playing</p>
              </div>
            </Card>
          ) : (
            <div className="grid gap-4">
              {activeGames.map(game => {
                const Icon = getGameIcon(game.game_type)
                return (
                  <Card key={game.id} className="hover:border-dark-700 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getGameColor(game.game_type)} flex items-center justify-center`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-white">{getGameName(game.game_type)}</h4>
                          <div className="flex items-center gap-2 mt-1 text-sm text-dark-400">
                            <Users className="w-4 h-4" />
                            {game.players.length} players
                            <span className="mx-1">•</span>
                            <Clock className="w-4 h-4" />
                            {new Date(game.created_at).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-lg text-sm ${
                        game.status === 'waiting' ? 'bg-yellow-500/20 text-yellow-400' :
                        game.status === 'playing' ? 'bg-green-500/20 text-green-400' :
                        'bg-dark-700 text-dark-400'
                      }`}>
                        {game.status}
                      </span>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-dark-800">
                      <div className="flex flex-wrap gap-2">
                        {game.players.map(player => (
                          <div key={player.user_id} className="flex items-center gap-2 px-3 py-1.5 bg-dark-800/50 rounded-lg">
                            <div className="w-6 h-6 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-xs font-bold text-white">
                              {player.first_name.charAt(0)}
                            </div>
                            <span className="text-sm text-dark-300">{player.first_name}</span>
                            {player.is_ready && <span className="text-green-400 text-xs">✓</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Settings Modal */}
      <Modal
        isOpen={settingsModalOpen}
        onRequestClose={() => setSettingsModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800 max-h-[90vh] overflow-y-auto">
          <h2 className="text-xl font-bold text-white mb-6">Game Settings</h2>
          
          {config && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div>
                  <p className="text-white font-medium">Rewards Enabled</p>
                  <p className="text-dark-400 text-sm">Allow players to earn rewards</p>
                </div>
                <button
                  onClick={() => setConfig({ ...config, rewards_enabled: !config.rewards_enabled })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    config.rewards_enabled ? 'bg-green-500' : 'bg-dark-700'
                  }`}
                >
                  <span className={`block w-5 h-5 bg-white rounded-full transition-transform ${
                    config.rewards_enabled ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Min Bet</label>
                  <input
                    type="number"
                    value={config.min_bet}
                    onChange={(e) => setConfig({ ...config, min_bet: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
                <div className="p-4 bg-dark-800/50 rounded-xl">
                  <label className="block text-dark-400 text-sm mb-2">Max Bet</label>
                  <input
                    type="number"
                    value={config.max_bet}
                    onChange={(e) => setConfig({ ...config, max_bet: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                  />
                </div>
              </div>

              <div className="p-4 bg-dark-800/50 rounded-xl">
                <label className="block text-dark-400 text-sm mb-2">Cooldown (seconds)</label>
                <input
                  type="number"
                  value={config.cooldown_seconds}
                  onChange={(e) => setConfig({ ...config, cooldown_seconds: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                />
              </div>

              <div className="p-4 bg-dark-800/50 rounded-xl">
                <label className="block text-dark-400 text-sm mb-2">Daily Game Limit</label>
                <input
                  type="number"
                  value={config.daily_game_limit}
                  onChange={(e) => setConfig({ ...config, daily_game_limit: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                />
              </div>

              <div className="p-4 bg-dark-800/50 rounded-xl">
                <label className="block text-dark-400 text-sm mb-2">House Edge (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.house_edge_percent}
                  onChange={(e) => setConfig({ ...config, house_edge_percent: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white"
                />
              </div>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setSettingsModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={saveSettings}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors"
            >
              Save Settings
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
