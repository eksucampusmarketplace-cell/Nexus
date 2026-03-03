import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Bot,
  Key,
  Check,
  X,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Shield,
  Copy,
  Trash2,
  Plus,
} from 'lucide-react'
import { getBotToken, registerBotToken, revokeBotToken, validateBotToken } from '../../api/botToken'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'
import Modal from 'react-modal'

Modal.setAppElement('#root')

export default function CustomBotToken() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [botToken, setBotToken] = useState<{
    bot_telegram_id: number
    bot_username: string
    bot_name: string
    is_active: boolean
    registered_at: string
  } | null>(null)
  const [tokenInput, setTokenInput] = useState('')
  const [validating, setValidating] = useState(false)
  const [validatedBot, setValidatedBot] = useState<{
    id: number
    username: string
    name: string
  } | null>(null)
  const [validationError, setValidationError] = useState('')
  const [registering, setRegistering] = useState(false)
  const [showConfirmRevoke, setShowConfirmRevoke] = useState(false)

  const loadBotToken = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const data = await getBotToken(parseInt(groupId))
      setBotToken(data)

      // Also load token from localStorage (for authentication purposes)
      if (!data) {
        const storedTokens = JSON.parse(localStorage.getItem('nexus_custom_bot_tokens') || '{}')
        if (storedTokens[groupId]) {
          // Token exists in localStorage but not registered in backend
          // This can happen if user cleared browser data but localStorage persists
          console.log('Found token in localStorage but not registered in backend')
        }
      }
    } catch (error) {
      setBotToken(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBotToken()
  }, [groupId])

  const handleValidate = async () => {
    if (!tokenInput) return
    setValidating(true)
    setValidationError('')
    setValidatedBot(null)
    try {
      const result = await validateBotToken(tokenInput)
      if (result.valid && result.bot) {
        setValidatedBot(result.bot)
      } else {
        setValidationError(result.error || 'Invalid token')
      }
    } catch (error) {
      setValidationError('Failed to validate token')
    } finally {
      setValidating(false)
    }
  }

  const handleRegister = async () => {
    if (!groupId || !tokenInput) return
    setRegistering(true)
    try {
      const result = await registerBotToken(parseInt(groupId), tokenInput)
      setBotToken(result)
      setTokenInput('')
      setValidatedBot(null)
      toast.success('Bot token registered successfully!')

      // Store the bot token in localStorage for authentication
      const storedTokens = JSON.parse(localStorage.getItem('nexus_custom_bot_tokens') || '{}')
      storedTokens[groupId] = tokenInput
      localStorage.setItem('nexus_custom_bot_tokens', JSON.stringify(storedTokens))
    } catch (error) {
      toast.error('Failed to register token')
    } finally {
      setRegistering(false)
    }
  }

  const handleRevoke = async () => {
    if (!groupId) return
    try {
      await revokeBotToken(parseInt(groupId))
      setBotToken(null)
      setShowConfirmRevoke(false)
      toast.success('Bot token revoked')

      // Remove the bot token from localStorage
      const storedTokens = JSON.parse(localStorage.getItem('nexus_custom_bot_tokens') || '{}')
      delete storedTokens[groupId]
      localStorage.setItem('nexus_custom_bot_tokens', JSON.stringify(storedTokens))
    } catch (error) {
      toast.error('Failed to revoke token')
    }
  }

  const openBotChat = () => {
    if (botToken?.bot_username) {
      window.open(`https://t.me/${botToken.bot_username}`, '_blank')
    }
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Custom Bot</h1>
        <p className="text-dark-400 mt-1">Use your own Telegram bot with Nexus</p>
      </div>

      {/* Current Bot */}
      {botToken && (
        <Card className="mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">{botToken.bot_name}</h3>
                <p className="text-dark-400">@{botToken.bot_username}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {botToken.is_active ? (
                <span className="flex items-center gap-1 px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">
                  <span className="w-2 h-2 bg-green-400 rounded-full" />
                  Active
                </span>
              ) : (
                <span className="flex items-center gap-1 px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm">
                  <span className="w-2 h-2 bg-red-400 rounded-full" />
                  Inactive
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-3 bg-dark-800 rounded-lg">
              <p className="text-dark-500 text-xs">Bot ID</p>
              <p className="text-white font-mono">{botToken.bot_telegram_id}</p>
            </div>
            <div className="p-3 bg-dark-800 rounded-lg">
              <p className="text-dark-500 text-xs">Registered</p>
              <p className="text-white">{new Date(botToken.registered_at).toLocaleDateString()}</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={openBotChat}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Open Bot
            </button>
            <button
              onClick={() => setShowConfirmRevoke(true)}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-red-600/20 hover:bg-red-600/30 rounded-xl text-red-400 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Revoke
            </button>
          </div>
        </Card>
      )}

      {/* Info Card */}
      <Card className="mb-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-500/20 rounded-lg">
            <Shield className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white mb-1">What is Custom Bot?</h3>
            <p className="text-dark-400 text-sm">
              Use your own Telegram bot token created via @BotFather. The bot will appear as your own
              bot in the group, with your bot's name and photo. All Nexus features work seamlessly
              with your custom bot.
            </p>
          </div>
        </div>
      </Card>

      {/* Register New Token */}
      {!botToken && (
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Register Custom Bot</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Bot Token
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={tokenInput}
                  onChange={(e) => {
                    setTokenInput(e.target.value)
                    setValidatedBot(null)
                    setValidationError('')
                  }}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 font-mono"
                />
                <button
                  onClick={handleValidate}
                  disabled={!tokenInput || validating}
                  className="px-6 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white disabled:opacity-50"
                >
                  {validating ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Validate'}
                </button>
              </div>
            </div>

            {validationError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-400" />
                <span className="text-red-400 text-sm">{validationError}</span>
              </div>
            )}

            {validatedBot && (
              <div className="p-4 bg-green-500/20 border border-green-500/30 rounded-xl">
                <div className="flex items-center gap-3 mb-3">
                  <Check className="w-5 h-5 text-green-400" />
                  <span className="text-green-400 font-medium">Token Validated!</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{validatedBot.name}</p>
                    <p className="text-dark-400 text-sm">@{validatedBot.username}</p>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={handleRegister}
              disabled={!validatedBot || registering}
              className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {registering ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Plus className="w-5 h-5" />
              )}
              {registering ? 'Registering...' : 'Register Bot'}
            </button>
          </div>
        </Card>
      )}

      {/* How to get token */}
      {!botToken && (
        <Card className="mt-6">
          <h3 className="text-lg font-semibold text-white mb-4">How to get a Bot Token</h3>
          <ol className="space-y-3 text-dark-300">
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0">
                1
              </span>
              <span>Open @BotFather on Telegram</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0">
                2
              </span>
              <span>Use /newbot command to create a new bot</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0">
                3
              </span>
              <span>Follow the instructions and get your bot token</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0">
                4
              </span>
              <span>Paste the token above and click Validate</span>
            </li>
          </ol>
          <a
            href="https://t.me/BotFather"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex items-center justify-center gap-2 px-4 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Open BotFather
          </a>
        </Card>
      )}

      {/* Confirm Revoke Modal */}
      <Modal
        isOpen={showConfirmRevoke}
        onRequestClose={() => setShowConfirmRevoke(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-red-500/20 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Revoke Bot Token?</h2>
          </div>
          <p className="text-dark-400 mb-6">
            This will disconnect your custom bot from this group. You can always register a new bot
            token later. The bot will stop responding to this group.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => setShowConfirmRevoke(false)}
              className="flex-1 px-4 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleRevoke}
              className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 rounded-xl text-white"
            >
              Revoke
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
