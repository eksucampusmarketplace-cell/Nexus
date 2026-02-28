import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Wallet,
  TrendingUp,
  Gift,
  ArrowRightLeft,
  Trophy,
  Banknote,
  ShoppingCart,
  History,
  Settings,
  DollarSign,
  Users,
  Coins,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Zap,
  Target,
  Crown,
  Star,
} from 'lucide-react'
import api from '../api/client'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Badge from '../../components/UI/Badge'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'

Modal.setAppElement('#root')

interface WalletData {
  id: number
  balance: number
  bank_balance: number
  loan_amount: number
  total_earned: number
  total_spent: number
  last_daily: string | null
  last_work: string | null
  last_crime: string | null
}

interface EconomyConfig {
  currency_name: string
  currency_emoji: string
  earn_per_message: number
  earn_per_reaction: number
  daily_bonus: number
  work_cooldown: number
  crime_cooldown: number
  daily_cooldown: number
}

interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string | null
  first_name: string
  balance: number
  bank_balance: number
  total_assets: number
}

interface ShopItem {
  id: number
  name: string
  description: string
  price: number
  emoji: string
  category: string
}

interface Transaction {
  id: number
  amount: number
  type: string
  reason: string
  is_incoming: boolean
  created_at: string
}

interface EconomyStats {
  total_supply: number
  total_transactions: number
  total_wallets: number
  daily_volume: number
  richest_user: {
    user_id: number
    username: string | null
    first_name: string
    balance: number
  } | null
}

export default function Economy() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'wallet' | 'leaderboard' | 'shop' | 'transactions' | 'settings'>('wallet')
  
  // Data states
  const [wallet, setWallet] = useState<WalletData | null>(null)
  const [config, setConfig] = useState<EconomyConfig | null>(null)
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [shopItems, setShopItems] = useState<ShopItem[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [stats, setStats] = useState<EconomyStats | null>(null)
  
  // Modal states
  const [transferModalOpen, setTransferModalOpen] = useState(false)
  const [bankModalOpen, setBankModalOpen] = useState(false)
  const [loanModalOpen, setLoanModalOpen] = useState(false)
  const [transferAmount, setTransferAmount] = useState('')
  const [transferToUser, setTransferToUser] = useState('')
  const [bankAmount, setBankAmount] = useState('')
  const [bankAction, setBankAction] = useState<'deposit' | 'withdraw'>('deposit')
  const [loadingAction, setLoadingAction] = useState(false)

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)
    
    try {
      const [walletRes, configRes, leaderboardRes, shopRes, statsRes, txRes] = await Promise.all([
        api.get(`/economy/wallet`),
        api.get(`/economy/config`),
        api.get(`/economy/leaderboard`, { params: { limit: 10 } }),
        api.get(`/economy/shop`),
        api.get(`/economy/stats`),
        api.get(`/economy/transactions`, { params: { page_size: 10 } }),
      ])
      
      setWallet(walletRes.data)
      setConfig(configRes.data)
      setLeaderboard(leaderboardRes.data || [])
      setShopItems(shopRes.data || [])
      setStats(statsRes.data)
      setTransactions(txRes.data.items || [])
    } catch (error) {
      console.error('Failed to load economy data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [groupId])

  const handleTransfer = async () => {
    if (!groupId || !transferAmount || !transferToUser) return
    
    setLoadingAction(true)
    try {
      await api.post('/economy/transfer', {
        amount: parseInt(transferAmount),
        to_user_id: parseInt(transferToUser),
        reason: 'transfer',
      })
      setTransferModalOpen(false)
      setTransferAmount('')
      setTransferToUser('')
      loadData()
    } catch (error) {
      console.error('Transfer failed:', error)
    } finally {
      setLoadingAction(false)
    }
  }

  const handleBankAction = async () => {
    if (!groupId || !bankAmount) return
    
    setLoadingAction(true)
    try {
      const endpoint = bankAction === 'deposit' ? '/economy/deposit' : '/economy/withdraw'
      await api.post(endpoint, { amount: parseInt(bankAmount) })
      setBankModalOpen(false)
      setBankAmount('')
      loadData()
    } catch (error) {
      console.error('Bank action failed:', error)
    } finally {
      setLoadingAction(false)
    }
  }

  const handleDaily = async () => {
    if (!groupId) return
    
    setLoadingAction(true)
    try {
      await api.post('/economy/daily')
      loadData()
    } catch (error) {
      console.error('Daily bonus failed:', error)
    } finally {
      setLoadingAction(false)
    }
  }

  const handleWork = async () => {
    if (!groupId) return
    
    setLoadingAction(true)
    try {
      await api.post('/economy/work')
      loadData()
    } catch (error) {
      console.error('Work failed:', error)
    } finally {
      setLoadingAction(false)
    }
  }

  const handleBuy = async (itemId: number, price: number) => {
    if (!groupId) return
    if (!confirm(`Buy this item for ${price} coins?`)) return
    
    try {
      await api.post(`/economy/buy/${itemId}`)
      loadData()
    } catch (error) {
      console.error('Purchase failed:', error)
    }
  }

  if (loading) {
    return <Loading />
  }

  const currency = config?.currency_emoji || '🪙'
  const currencyName = config?.currency_name || 'coins'

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Economy</h1>
        <p className="text-dark-400 mt-1">
          Virtual currency and rewards system
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {[
          { id: 'wallet', label: 'Wallet', icon: Wallet },
          { id: 'leaderboard', label: 'Leaderboard', icon: Trophy },
          { id: 'shop', label: 'Shop', icon: ShoppingCart },
          { id: 'transactions', label: 'History', icon: History },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Wallet Tab */}
      {activeTab === 'wallet' && wallet && (
        <div className="space-y-6">
          {/* Balance Card */}
          <Card className="bg-gradient-to-br from-primary-500/20 to-accent-500/20 border-primary-500/30">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 bg-primary-500/30 rounded-2xl flex items-center justify-center">
                  <Wallet className="w-7 h-7 text-primary-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Your Wallet</h3>
                  <p className="text-dark-400 text-sm">{currencyName}</p>
                </div>
              </div>
              <button
                onClick={handleDaily}
                disabled={loadingAction}
                className="px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-xl font-medium transition-colors disabled:opacity-50"
              >
                <Gift className="w-4 h-4 inline mr-1" />
                Daily
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-dark-900/50 rounded-xl p-4">
                <p className="text-dark-400 text-sm mb-1">Cash</p>
                <p className="text-2xl font-bold text-white">
                  {wallet.balance.toLocaleString()} {currency}
                </p>
              </div>
              <div className="bg-dark-900/50 rounded-xl p-4">
                <p className="text-dark-400 text-sm mb-1">Bank</p>
                <p className="text-2xl font-bold text-white">
                  {wallet.bank_balance.toLocaleString()} {currency}
                </p>
              </div>
            </div>

            {wallet.loan_amount > 0 && (
              <div className="mt-4 p-3 bg-red-500/20 rounded-xl flex items-center justify-between">
                <span className="text-red-400">Outstanding Loan</span>
                <span className="font-bold text-white">{wallet.loan_amount.toLocaleString()} {currency}</span>
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => { setBankAction('deposit'); setBankModalOpen(true) }}
                className="flex-1 py-2 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
              >
                <ArrowDownRight className="w-4 h-4 inline mr-1" />
                Deposit
              </button>
              <button
                onClick={() => { setBankAction('withdraw'); setBankModalOpen(true) }}
                className="flex-1 py-2 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
              >
                <ArrowUpRight className="w-4 h-4 inline mr-1" />
                Withdraw
              </button>
              <button
                onClick={() => setLoanModalOpen(true)}
                className="flex-1 py-2 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
              >
                <Banknote className="w-4 h-4 inline mr-1" />
                Loan
              </button>
            </div>
          </Card>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleWork}
              disabled={loadingAction}
              className="p-4 bg-dark-800 hover:bg-dark-700 rounded-xl transition-colors disabled:opacity-50"
            >
              <Zap className="w-5 h-5 text-yellow-400 mx-auto mb-2" />
              <p className="text-white font-medium">Work</p>
              <p className="text-dark-400 text-xs">Earn 10-50 {currencyName}</p>
            </button>
            <button
              onClick={() => setTransferModalOpen(true)}
              className="p-4 bg-dark-800 hover:bg-dark-700 rounded-xl transition-colors"
            >
              <ArrowRightLeft className="w-5 h-5 text-primary-400 mx-auto mb-2" />
              <p className="text-white font-medium">Transfer</p>
              <p className="text-dark-400 text-xs">Send to another user</p>
            </button>
          </div>

          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-2 gap-4">
              <StatCard
                title="Total Supply"
                value={stats.total_supply.toLocaleString()}
                icon={Coins}
              />
              <StatCard
                title="Daily Volume"
                value={stats.daily_volume.toLocaleString()}
                icon={TrendingUp}
              />
            </div>
          )}
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <Card title="Top Holders" icon={Trophy}>
          <div className="space-y-3 mt-4">
            {leaderboard.length === 0 ? (
              <p className="text-dark-400 text-center py-8">No wallets yet</p>
            ) : (
              leaderboard.map((user, index) => (
                <div key={user.user_id} className="flex items-center gap-3 p-3 bg-dark-800/50 rounded-xl">
                  <span className={`
                    w-8 text-center font-bold
                    ${index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-300' : index === 2 ? 'text-orange-400' : 'text-dark-500'}
                  `}>
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${user.rank}`}
                  </span>
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                    {user.first_name?.charAt(0) || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {user.username ? `@${user.username}` : user.first_name}
                    </p>
                    <p className="text-dark-400 text-xs">
                      Bank: {user.bank_balance.toLocaleString()} {currency}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-white">{user.balance.toLocaleString()}</p>
                    <p className="text-dark-400 text-xs">{currency}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Shop Tab */}
      {activeTab === 'shop' && (
        <Card title="Item Shop" icon={ShoppingCart}>
          <div className="grid gap-3 mt-4">
            {shopItems.map(item => (
              <div key={item.id} className="flex items-center justify-between p-4 bg-dark-800/50 rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{item.emoji}</span>
                  <div>
                    <p className="text-white font-medium">{item.name}</p>
                    <p className="text-dark-400 text-xs">{item.description}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleBuy(item.id, item.price)}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white font-medium transition-colors"
                >
                  {item.price.toLocaleString()} {currency}
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Transactions Tab */}
      {activeTab === 'transactions' && (
        <Card title="Transaction History" icon={History}>
          <div className="space-y-3 mt-4">
            {transactions.length === 0 ? (
              <p className="text-dark-400 text-center py-8">No transactions yet</p>
            ) : (
              transactions.map(tx => (
                <div key={tx.id} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      tx.is_incoming ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                      {tx.is_incoming ? (
                        <ArrowDownRight className="w-5 h-5 text-green-400" />
                      ) : (
                        <ArrowUpRight className="w-5 h-5 text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-white font-medium capitalize">{tx.type}</p>
                      <p className="text-dark-400 text-xs">{tx.reason}</p>
                    </div>
                  </div>
                  <span className={`font-bold ${tx.is_incoming ? 'text-green-400' : 'text-red-400'}`}>
                    {tx.is_incoming ? '+' : '-'}{tx.amount.toLocaleString()} {currency}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && config && (
        <Card title="Economy Settings" icon={Settings}>
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between py-3 border-b border-dark-700">
              <span className="text-dark-300">Currency Name</span>
              <span className="font-medium text-white">{config.currency_name} {currency}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-dark-700">
              <span className="text-dark-300">Earn per Message</span>
              <span className="font-medium text-white">{config.earn_per_message} {currency}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-dark-700">
              <span className="text-dark-300">Earn per Reaction</span>
              <span className="font-medium text-white">{config.earn_per_reaction} {currency}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-dark-700">
              <span className="text-dark-300">Daily Bonus</span>
              <span className="font-medium text-white">{config.daily_bonus} {currency}</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-dark-700">
              <span className="text-dark-300">Work Cooldown</span>
              <span className="font-medium text-white">{Math.floor(config.work_cooldown / 60)} min</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-dark-300">Daily Cooldown</span>
              <span className="font-medium text-white">{Math.floor(config.daily_cooldown / 3600)} hours</span>
            </div>
          </div>
        </Card>
      )}

      {/* Transfer Modal */}
      <Modal
        isOpen={transferModalOpen}
        onRequestClose={() => setTransferModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Transfer Coins</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Recipient User ID
              </label>
              <input
                type="number"
                value={transferToUser}
                onChange={(e) => setTransferToUser(e.target.value)}
                placeholder="Enter user ID"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Amount
              </label>
              <input
                type="number"
                value={transferAmount}
                onChange={(e) => setTransferAmount(e.target.value)}
                placeholder="Amount to transfer"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setTransferModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleTransfer}
              disabled={loadingAction || !transferAmount || !transferToUser}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Transfer
            </button>
          </div>
        </div>
      </Modal>

      {/* Bank Modal */}
      <Modal
        isOpen={bankModalOpen}
        onRequestClose={() => setBankModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">
            {bankAction === 'deposit' ? 'Deposit to Bank' : 'Withdraw from Bank'}
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Amount
              </label>
              <input
                type="number"
                value={bankAmount}
                onChange={(e) => setBankAmount(e.target.value)}
                placeholder="Amount"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setBankModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleBankAction}
              disabled={loadingAction || !bankAmount}
              className="flex-1 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              {bankAction === 'deposit' ? 'Deposit' : 'Withdraw'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Loan Modal */}
      <Modal
        isOpen={loanModalOpen}
        onRequestClose={() => setLoanModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-4">Get a Loan</h2>
          <p className="text-dark-400 mb-6">
            Take a loan of up to 10,000 coins with 5% interest. Repay in monthly installments.
          </p>
          
          <div className="bg-dark-800 rounded-xl p-4 mb-6">
            <div className="flex justify-between mb-2">
              <span className="text-dark-400">Your current loan</span>
              <span className="text-white font-medium">{wallet?.loan_amount || 0} {currency}</span>
            </div>
            {(wallet?.loan_amount || 0) > 0 && (
              <button className="w-full py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white font-medium transition-colors">
                Repay Loan
              </button>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setLoanModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
