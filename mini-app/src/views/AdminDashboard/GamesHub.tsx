import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Gamepad2, Trophy, Users, Zap, BarChart3 } from 'lucide-react'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Toggle from '../../components/UI/Toggle'
import Badge from '../../components/UI/Badge'

const availableGames = [
  { id: 'trivia', name: 'Trivia', description: 'Answer trivia questions', icon: '🧠', players: 423 },
  { id: 'wordle', name: 'Wordle', description: 'Guess the hidden word', icon: '📝', players: 287 },
  { id: 'math', name: 'Math Battle', description: 'Solve math problems fastest', icon: '🔢', players: 195 },
  { id: 'hangman', name: 'Hangman', description: 'Classic word guessing game', icon: '🎯', players: 164 },
  { id: 'rps', name: 'Rock Paper Scissors', description: 'Classic hand game', icon: '✂️', players: 312 },
  { id: 'slots', name: 'Slot Machine', description: 'Test your luck', icon: '🎰', players: 521 },
  { id: 'dice', name: 'Dice Roll', description: 'Roll the dice challenge', icon: '🎲', players: 398 },
  { id: 'quiz', name: 'Custom Quiz', description: 'Admin-created quizzes', icon: '📋', players: 148 },
]

const leaderboard = [
  { rank: 1, name: 'Alex', username: 'alex_dev', score: 4820, wins: 47 },
  { rank: 2, name: 'Sarah', username: 'sarah_k', score: 4350, wins: 39 },
  { rank: 3, name: 'Mike', username: 'mike_99', score: 3910, wins: 34 },
  { rank: 4, name: 'Emma', username: 'emma_j', score: 3240, wins: 28 },
  { rank: 5, name: 'Tom', username: 'tomcat', score: 2870, wins: 21 },
]

export default function GamesHub() {
  const { groupId } = useParams<{ groupId: string }>()
  const [enabledGames, setEnabledGames] = useState<Record<string, boolean>>(
    Object.fromEntries(availableGames.map(g => [g.id, true]))
  )
  const [awardXP, setAwardXP] = useState(true)
  const [awardCoins, setAwardCoins] = useState(true)
  const [activeTab, setActiveTab] = useState<'games' | 'leaderboard'>('games')

  const toggleGame = (id: string) => {
    setEnabledGames(prev => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Games Hub</h1>
        <p className="text-dark-400 mt-1">Manage group games and leaderboards</p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatCard title="Active Games" value={String(Object.values(enabledGames).filter(Boolean).length)} icon={Gamepad2} />
        <StatCard title="Total Players" value="1.2k" icon={Users} />
        <StatCard title="Games Played" value="4.8k" icon={BarChart3} />
        <StatCard title="Top Score" value="4820" icon={Trophy} />
      </div>

      <div className="flex gap-2 mb-6">
        {(['games', 'leaderboard'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              activeTab === tab ? 'bg-primary-600 text-white' : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'games' && (
        <>
          <Card title="Rewards" icon={Zap} className="mb-6">
            <div className="space-y-3 mt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white text-sm font-medium">Award XP for Wins</p>
                  <p className="text-dark-400 text-xs">Players earn experience points</p>
                </div>
                <Toggle checked={awardXP} onChange={setAwardXP} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white text-sm font-medium">Award Coins for Wins</p>
                  <p className="text-dark-400 text-xs">Players earn virtual currency</p>
                </div>
                <Toggle checked={awardCoins} onChange={setAwardCoins} />
              </div>
            </div>
          </Card>

          <Card title="Available Games" icon={Gamepad2}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
              {availableGames.map(game => (
                <div
                  key={game.id}
                  className="bg-dark-800 rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{game.icon}</span>
                    <div>
                      <p className="text-white text-sm font-medium">{game.name}</p>
                      <p className="text-dark-500 text-xs">{game.players} played</p>
                    </div>
                  </div>
                  <Toggle checked={enabledGames[game.id]} onChange={() => toggleGame(game.id)} />
                </div>
              ))}
            </div>
          </Card>
        </>
      )}

      {activeTab === 'leaderboard' && (
        <Card title="Top Players" icon={Trophy}>
          <div className="space-y-3 mt-4">
            {leaderboard.map(player => (
              <div
                key={player.rank}
                className="flex items-center gap-4 bg-dark-800 rounded-lg p-4"
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  player.rank === 1 ? 'bg-yellow-500 text-black' :
                  player.rank === 2 ? 'bg-gray-400 text-black' :
                  player.rank === 3 ? 'bg-amber-600 text-white' :
                  'bg-dark-700 text-dark-300'
                }`}>
                  {player.rank}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium">{player.name}</p>
                  <p className="text-dark-400 text-xs">@{player.username}</p>
                </div>
                <div className="text-right">
                  <p className="text-white text-sm font-semibold">{player.score.toLocaleString()}</p>
                  <Badge variant="default">{player.wins} wins</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
