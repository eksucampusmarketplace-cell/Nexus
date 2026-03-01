import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, Settings, MessageSquare, Lock, FileText,
  Filter, FileCheck, Coins, TrendingUp, Calendar,
  User, Users, Zap, Gamepad2, BarChart3, Bot,
  Info, PieChart, Trash2, Sparkles, Volume2, CheckCircle, LucideIcon
} from 'lucide-react'
import Card from '../components/UI/Card'

interface Command {
  name: string
  description: string
  adminOnly: boolean
  aliases?: string[]
}

interface Category {
  icon: LucideIcon
  color: string
  bgColor: string
  commands: Command[]
}

// Type assertion to ensure all commands have the same type
type CommandCategories = Record<string, Category>

const commandCategories: Record<string, Category> = {
  "Core": {
    icon: Settings,
    color: "text-blue-500",
    bgColor: "bg-blue-500/20",
    commands: [
      { name: "start", description: "Start bot and see welcome", adminOnly: false },
      { name: "help", description: "Show this help message", adminOnly: false },
      { name: "about", description: "About Nexus bot", adminOnly: false },
      { name: "ping", description: "Check bot latency", adminOnly: false },
      { name: "version", description: "Show bot version", adminOnly: false },
    ] as Command[]
  },
  "Moderation": {
    icon: Shield,
    color: "text-red-500",
    bgColor: "bg-red-500/20",
    commands: [
      { name: "warn", description: "Warn a user", adminOnly: true, aliases: ["w"] },
      { name: "warns", description: "View user's warnings", adminOnly: true },
      { name: "resetwarns", description: "Reset user's warnings", adminOnly: true },
      { name: "warnlimit", description: "Set warning threshold", adminOnly: true },
      { name: "warntime", description: "Set warning expiration", adminOnly: true },
      { name: "mute", description: "Mute a user", adminOnly: true, aliases: ["m", "tmute", "tm"] },
      { name: "unmute", description: "Unmute a user", adminOnly: true, aliases: ["um"] },
      { name: "ban", description: "Ban a user", adminOnly: true, aliases: ["b", "tban", "tb"] },
      { name: "unban", description: "Unban a user", adminOnly: true, aliases: ["ub"] },
      { name: "kick", description: "Kick a user", adminOnly: true, aliases: ["k", "kickme"] },
      { name: "promote", description: "Promote to admin/mod", adminOnly: true },
      { name: "demote", description: "Demote from admin/mod", adminOnly: true },
      { name: "pin", description: "Pin a message", adminOnly: true },
      { name: "unpin", description: "Unpin a message", adminOnly: true },
      { name: "purge", description: "Bulk delete messages", adminOnly: true },
      { name: "del", description: "Delete a message", adminOnly: true },
      { name: "history", description: "View user history", adminOnly: true },
      { name: "trust", description: "Trust a user", adminOnly: true },
      { name: "report", description: "Report to admins", adminOnly: false },
      { name: "slowmode", description: "Enable/disable slow mode", adminOnly: true },
    ] as Command[]
  },
  "Welcome": {
    icon: MessageSquare,
    color: "text-green-500",
    bgColor: "bg-green-500/20",
    commands: [
      { name: "setwelcome", description: "Set welcome message", adminOnly: true },
      { name: "welcome", description: "View welcome message", adminOnly: false },
      { name: "resetwelcome", description: "Reset welcome message", adminOnly: true },
      { name: "setgoodbye", description: "Set goodbye message", adminOnly: true },
      { name: "goodbye", description: "View goodbye message", adminOnly: false },
      { name: "resetgoodbye", description: "Reset goodbye message", adminOnly: true },
      { name: "cleanwelcome", description: "Toggle auto-delete welcome", adminOnly: true },
    ] as Command[]
  },
  "Locks": {
    icon: Lock,
    color: "text-orange-500",
    bgColor: "bg-orange-500/20",
    commands: [
      { name: "locktypes", description: "List all lock types", adminOnly: false },
      { name: "lock", description: "Lock content type", adminOnly: true },
      { name: "unlock", description: "Unlock content type", adminOnly: true },
      { name: "locks", description: "View all locks", adminOnly: false },
      { name: "lockall", description: "Lock all types", adminOnly: true },
      { name: "unlockall", description: "Unlock all types", adminOnly: true },
    ] as Command[]
  },
  "Notes": {
    icon: FileText,
    color: "text-purple-500",
    bgColor: "bg-purple-500/20",
    commands: [
      { name: "save", description: "Save note", adminOnly: false },
      { name: "note", description: "Retrieve note", adminOnly: false, aliases: ["get", "#"] },
      { name: "notes", description: "List all notes", adminOnly: false },
      { name: "clear", description: "Delete note", adminOnly: true },
      { name: "clearall", description: "Delete all notes", adminOnly: true },
    ] as Command[]
  },
  "Filters": {
    icon: Filter,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/20",
    commands: [
      { name: "filter", description: "Create filter", adminOnly: true },
      { name: "filters", description: "List all filters", adminOnly: true },
      { name: "stop", description: "Delete filter", adminOnly: true },
      { name: "stopall", description: "Delete all filters", adminOnly: true },
      { name: "filtermode", description: "Set filter mode", adminOnly: true },
    ] as Command[]
  },
  "Economy": {
    icon: Coins,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/20",
    commands: [
      { name: "balance", description: "Check wallet balance", adminOnly: false, aliases: ["bal", "wallet"] },
      { name: "daily", description: "Claim daily bonus", adminOnly: false },
      { name: "give", description: "Give coins to user", adminOnly: false, aliases: ["transfer", "pay"] },
      { name: "leaderboard", description: "View economy leaderboard", adminOnly: false, aliases: ["lb", "rich"] },
      { name: "shop", description: "View group shop", adminOnly: false },
      { name: "buy", description: "Purchase item", adminOnly: false },
      { name: "inventory", description: "View inventory", adminOnly: false, aliases: ["inv"] },
      { name: "coinflip", description: "Flip coin and bet", adminOnly: false },
      { name: "gamble", description: "50/50 gamble", adminOnly: false },
      { name: "rob", description: "Attempt robbery", adminOnly: false },
      { name: "work", description: "Work for coins", adminOnly: false },
      { name: "crime", description: "Commit crime", adminOnly: false },
      { name: "bank", description: "View bank balance", adminOnly: false },
    ] as Command[]
  },
  "Games": {
    icon: Gamepad2,
    color: "text-pink-500",
    bgColor: "bg-pink-500/20",
    commands: [
      { name: "trivia", description: "Start trivia quiz", adminOnly: false },
      { name: "wordle", description: "Start Wordle game", adminOnly: false },
      { name: "hangman", description: "Start Hangman game", adminOnly: false },
      { name: "8ball", description: "Ask magic 8-ball", adminOnly: false },
      { name: "roll", description: "Roll dice", adminOnly: false },
      { name: "flip", description: "Flip coin", adminOnly: false },
      { name: "rps", description: "Play rock-paper-scissors", adminOnly: false },
      { name: "dice", description: "Dice betting", adminOnly: false },
      { name: "slots", description: "Slot machine", adminOnly: false },
      { name: "tictactoe", description: "Play tic-tac-toe", adminOnly: false },
    ] as Command[]
  },
  "AI Assistant": {
    icon: Bot,
    color: "text-indigo-500",
    bgColor: "bg-indigo-500/20",
    commands: [
      { name: "ai", description: "Ask AI assistant", adminOnly: false },
      { name: "summarize", description: "Summarize messages", adminOnly: false },
      { name: "translate", description: "Translate text", adminOnly: false },
      { name: "draft", description: "Draft announcement (admin)", adminOnly: true },
    ] as Command[]
  },
  "Info": {
    icon: Info,
    color: "text-gray-500",
    bgColor: "bg-gray-500/20",
    commands: [
      { name: "info", description: "View user information", adminOnly: false },
      { name: "chatinfo", description: "View group information", adminOnly: false },
      { name: "id", description: "Get user or group ID", adminOnly: false },
    ] as Command[]
  },
}

export default function Help() {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)

  return (
    <div className="py-6 animate-fade-in space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-white">
          Nexus Bot Commands
        </h1>
        <p className="text-dark-400 max-w-2xl mx-auto">
          Browse through all available commands organized by category. Click on a category to expand and view its commands.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 text-center">
          <p className="text-2xl font-bold text-white">{Object.keys(commandCategories).length}</p>
          <p className="text-sm text-dark-400">Categories</p>
        </div>
        <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 text-center">
          <p className="text-2xl font-bold text-white">
            {Object.values(commandCategories).reduce((acc, cat) => acc + cat.commands.length, 0)}
          </p>
          <p className="text-sm text-dark-400">Commands</p>
        </div>
        <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 text-center">
          <p className="text-2xl font-bold text-white">
            {Object.values(commandCategories).reduce((acc, cat) => 
              acc + cat.commands.filter(cmd => !cmd.adminOnly).length, 0)
            }
          </p>
          <p className="text-sm text-dark-400">Public</p>
        </div>
        <div className="p-4 bg-dark-800 rounded-xl border border-dark-700 text-center">
          <p className="text-2xl font-bold text-white">
            {Object.values(commandCategories).reduce((acc, cat) => 
              acc + cat.commands.filter(cmd => cmd.adminOnly).length, 0)
            }
          </p>
          <p className="text-sm text-dark-400">Admin</p>
        </div>
      </div>

      {/* Command Categories */}
      <div className="space-y-3">
        {Object.entries(commandCategories).map(([categoryName, category]) => {
          const Icon = category.icon
          const isExpanded = expandedCategory === categoryName

          return (
            <motion.div
              key={categoryName}
              layout
              className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden"
            >
              <button
                onClick={() => setExpandedCategory(isExpanded ? null : categoryName)}
                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-dark-700/50 transition-colors"
              >
                <div className={`w-10 h-10 rounded-lg ${category.bgColor} ${category.color} flex items-center justify-center`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 text-left">
                  <h3 className="font-medium text-white">{categoryName}</h3>
                  <p className="text-sm text-dark-400">{category.commands.length} commands</p>
                </div>
                <motion.div
                  animate={{ rotate: isExpanded ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <CheckCircle className="w-5 h-5 text-dark-400" />
                </motion.div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-dark-700"
                  >
                    <div className="p-4 space-y-2">
                      {category.commands.map((command) => (
                        <div
                          key={command.name}
                          className="flex items-start gap-3 p-2 rounded-lg hover:bg-dark-700/30 transition-colors"
                        >
                          <code className="px-2 py-1 bg-dark-900 rounded text-sm text-primary-400 font-mono">
                            /{command.name}
                          </code>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-dark-300">{command.description}</p>
                            {command.aliases && (
                              <p className="text-xs text-dark-500 mt-0.5">
                                Aliases: {command.aliases.map(a => `/${a}`).join(', ')}
                              </p>
                            )}
                          </div>
                          {command.adminOnly && (
                            <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full whitespace-nowrap">
                              Admin
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      {/* Tips */}
      <Card className="mt-6">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-yellow-500" />
          Tips
        </h3>
        <ul className="space-y-2 text-sm text-dark-300">
          <li className="flex items-start gap-2">
            <span className="text-primary-500 mt-0.5">•</span>
            <span>Use <code className="px-1 bg-dark-900 rounded text-primary-400">/help &lt;command&gt;</code> in Telegram for detailed information about a specific command</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-500 mt-0.5">•</span>
            <span>Admin-only commands require you to be a group administrator</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-500 mt-0.5">•</span>
            <span>Many commands have shortcuts/aliases for faster typing</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-500 mt-0.5">•</span>
            <span>Use the Mini App for advanced features and visual management</span>
          </li>
        </ul>
      </Card>
    </div>
  )
}
