import { useState } from 'react'
import {
  Users,
  Key,
  HelpCircle,
  ArrowRight,
  Bot,
  Shield,
  ChevronRight,
  ExternalLink,
  Check,
  AlertTriangle,
  RefreshCw,
  Info,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import Card from '../components/UI/Card'

interface EntrySelectionProps {
  onSelectExistingGroups: () => void
  onSelectCustomToken: (token: string) => void
  onSelectFirstTime: () => void
  isLoading: boolean
  error?: string | null
}

type SelectionMode = 'main' | 'custom-token' | 'first-time' | 'help'

export default function EntrySelection({
  onSelectExistingGroups,
  onSelectCustomToken,
  onSelectFirstTime,
  isLoading,
  error,
}: EntrySelectionProps) {
  const [mode, setMode] = useState<SelectionMode>('main')
  const [tokenInput, setTokenInput] = useState('')
  const [tokenError, setTokenError] = useState('')

  const handleTokenSubmit = () => {
    if (!tokenInput.trim()) {
      setTokenError('Please enter a bot token')
      return
    }
    // Basic format validation (123456789:ABCdefGHIjkl...)
    const tokenPattern = /^\d+:[A-Za-z0-9_-]+$/
    if (!tokenPattern.test(tokenInput.trim())) {
      setTokenError('Invalid token format. Should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz')
      return
    }
    setTokenError('')
    onSelectCustomToken(tokenInput.trim())
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/20">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Nexus</h1>
          <p className="text-dark-400">Advanced Telegram Bot Platform</p>
        </div>

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                {error.includes('\n') ? (
                  <div className="text-red-400 text-sm whitespace-pre-line">{error}</div>
                ) : (
                  <p className="text-red-400 text-sm">{error}</p>
                )}
              </div>
            </div>
          </motion.div>
        )}

        <AnimatePresence mode="wait">
          {/* Main Selection Mode */}
          {mode === 'main' && (
            <motion.div
              key="main"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <Card className="p-1">
                {/* Option 1: Existing Groups */}
                <button
                  onClick={onSelectExistingGroups}
                  disabled={isLoading}
                  className="w-full p-4 flex items-center gap-4 hover:bg-dark-800/50 rounded-xl transition-colors text-left group disabled:opacity-50"
                >
                  <div className="w-12 h-12 rounded-xl bg-primary-600/20 flex items-center justify-center flex-shrink-0">
                    <Users className="w-6 h-6 text-primary-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                      Use Existing Groups
                      <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-white transition-colors" />
                    </h3>
                    <p className="text-dark-400 text-sm mt-0.5">
                      I already have groups with Nexus bot
                    </p>
                  </div>
                </button>

                <div className="h-px bg-dark-800 mx-4" />

                {/* Option 2: Custom Bot Token */}
                <button
                  onClick={() => setMode('custom-token')}
                  disabled={isLoading}
                  className="w-full p-4 flex items-center gap-4 hover:bg-dark-800/50 rounded-xl transition-colors text-left group disabled:opacity-50"
                >
                  <div className="w-12 h-12 rounded-xl bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                    <Key className="w-6 h-6 text-purple-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                      Add Custom Bot Token
                      <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-white transition-colors" />
                    </h3>
                    <p className="text-dark-400 text-sm mt-0.5">
                      I have my own bot from @BotFather
                    </p>
                  </div>
                </button>

                <div className="h-px bg-dark-800 mx-4" />

                {/* Option 3: First Time */}
                <button
                  onClick={() => setMode('first-time')}
                  disabled={isLoading}
                  className="w-full p-4 flex items-center gap-4 hover:bg-dark-800/50 rounded-xl transition-colors text-left group disabled:opacity-50"
                >
                  <div className="w-12 h-12 rounded-xl bg-green-600/20 flex items-center justify-center flex-shrink-0">
                    <HelpCircle className="w-6 h-6 text-green-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                      First Time Setup
                      <ChevronRight className="w-4 h-4 text-dark-500 group-hover:text-white transition-colors" />
                    </h3>
                    <p className="text-dark-400 text-sm mt-0.5">
                      I'm new and need help getting started
                    </p>
                  </div>
                </button>
              </Card>

              {/* Help Button */}
              <button
                onClick={() => setMode('help')}
                className="w-full p-4 flex items-center justify-center gap-2 text-dark-400 hover:text-white transition-colors"
              >
                <Info className="w-4 h-4" />
                <span className="text-sm">What is this?</span>
              </button>

              {/* Debug Button (development only) */}
              {import.meta.env.DEV && (
                <button
                  onClick={async () => {
                    try {
                      const response = await fetch('/api/diagnostic')
                      const data = await response.json()
                      alert(JSON.stringify(data, null, 2))
                    } catch (e) {
                      alert('Failed to get diagnostic info: ' + e)
                    }
                  }}
                  className="w-full p-2 flex items-center justify-center gap-2 text-dark-500 hover:text-dark-300 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span className="text-xs">Debug Info (Dev)</span>
                </button>
              )}
            </motion.div>
          )}

          {/* Custom Token Mode */}
          {mode === 'custom-token' && (
            <motion.div
              key="custom-token"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <button
                    onClick={() => setMode('main')}
                    className="p-2 -ml-2 hover:bg-dark-800 rounded-lg transition-colors"
                  >
                    <ArrowRight className="w-5 h-5 text-dark-400 rotate-180" />
                  </button>
                  <h2 className="text-lg font-semibold text-white">Enter Bot Token</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-2">
                      Your Bot Token from @BotFather
                    </label>
                    <input
                      type="text"
                      value={tokenInput}
                      onChange={(e) => {
                        setTokenInput(e.target.value)
                        setTokenError('')
                      }}
                      placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                      className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 font-mono text-sm"
                      disabled={isLoading}
                    />
                    {tokenError && (
                      <p className="mt-2 text-red-400 text-sm flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4" />
                        {tokenError}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handleTokenSubmit}
                    disabled={isLoading || !tokenInput.trim()}
                    className="w-full py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        Authenticating...
                      </>
                    ) : (
                      <>
                        Continue
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </div>
              </Card>

              {/* How to get token */}
              <Card className="p-4">
                <h3 className="text-sm font-medium text-white mb-3">How to get a bot token:</h3>
                <ol className="space-y-2 text-dark-400 text-sm">
                  <li className="flex gap-2">
                    <span className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0">
                      1
                    </span>
                    Open @BotFather on Telegram
                  </li>
                  <li className="flex gap-2">
                    <span className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0">
                      2
                    </span>
                    Use /newbot command
                  </li>
                  <li className="flex gap-2">
                    <span className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0">
                      3
                    </span>
                    Follow instructions to create bot
                  </li>
                  <li className="flex gap-2">
                    <span className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0">
                      4
                    </span>
                    Copy the token and paste here
                  </li>
                </ol>
                <a
                  href="https://t.me/BotFather"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 flex items-center justify-center gap-2 px-4 py-2 bg-dark-800 hover:bg-dark-700 rounded-lg text-white text-sm transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open BotFather
                </a>
              </Card>
            </motion.div>
          )}

          {/* First Time Setup Mode */}
          {mode === 'first-time' && (
            <motion.div
              key="first-time"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <button
                    onClick={() => setMode('main')}
                    className="p-2 -ml-2 hover:bg-dark-800 rounded-lg transition-colors"
                  >
                    <ArrowRight className="w-5 h-5 text-dark-400 rotate-180" />
                  </button>
                  <h2 className="text-lg font-semibold text-white">Getting Started</h2>
                </div>

                <div className="space-y-6">
                  {/* Step 1 */}
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                      1
                    </div>
                    <div>
                      <h3 className="font-medium text-white mb-1">Add Bot to Your Group</h3>
                      <p className="text-dark-400 text-sm">
                        Open your Telegram group, click group name → Members → Add members, and search for <strong className="text-white">@NexusPowerfulbot</strong>.
                      </p>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                      2
                    </div>
                    <div>
                      <h3 className="font-medium text-white mb-1">Send a Message</h3>
                      <p className="text-dark-400 text-sm">
                        Send any message in the group to register yourself as a member.
                      </p>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-semibold flex-shrink-0">
                      3
                    </div>
                    <div>
                      <h3 className="font-medium text-white mb-1">Open from the Group</h3>
                      <p className="text-dark-400 text-sm">
                        Click the menu (⋮) in your group and select "Mini App" or use a command like /dashboard
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-dark-800 rounded-xl">
                  <p className="text-dark-300 text-sm">
                    <strong className="text-white">Alternative:</strong> If you have your own bot from @BotFather, select "Add Custom Bot Token" instead and enter your bot token.
                  </p>
                </div>
              </Card>

              <button
                onClick={() => setMode('custom-token')}
                className="w-full py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-white font-medium transition-colors"
              >
                I Have My Own Bot Token
              </button>
            </motion.div>
          )}

          {/* Help Mode */}
          {mode === 'help' && (
            <motion.div
              key="help"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <button
                    onClick={() => setMode('main')}
                    className="p-2 -ml-2 hover:bg-dark-800 rounded-lg transition-colors"
                  >
                    <ArrowRight className="w-5 h-5 text-dark-400 rotate-180" />
                  </button>
                  <h2 className="text-lg font-semibold text-white">About Nexus</h2>
                </div>

                <div className="space-y-4 text-dark-300 text-sm">
                  <p>
                    <strong className="text-white">Nexus</strong> is an advanced Telegram bot platform for group management, featuring:
                  </p>
                  <ul className="space-y-2 list-disc list-inside">
                    <li>Moderation tools (ban, mute, warn)</li>
                    <li>Custom commands and auto-responses</li>
                    <li>Economy system with points and levels</li>
                    <li>Games and entertainment modules</li>
                    <li>AI-powered features</li>
                    <li>Analytics and insights</li>
                  </ul>
                  <p>
                    You can use Nexus in two ways:
                  </p>
                  <div className="space-y-2">
                    <div className="p-3 bg-dark-800 rounded-lg">
                      <strong className="text-white">Shared Bot:</strong> Add the main Nexus bot to your group
                    </div>
                    <div className="p-3 bg-dark-800 rounded-lg">
                      <strong className="text-white">Custom Bot:</strong> Use your own bot from @BotFather with Nexus features
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <p className="text-center text-dark-500 text-xs mt-8">
          Powered by Nexus Bot Platform
        </p>
      </div>
    </div>
  )
}
