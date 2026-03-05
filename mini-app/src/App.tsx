import { useEffect, useState, useCallback } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'
import { getGroupByTelegramId, getGroupStatsByTelegramId } from './api/groups'

// Enhanced Debug System - Import both old and new for compatibility
import {
  enhancedDebug,
  telegramDebug,
  InitDataValidator,
  ErrorAnalyzer,
  ErrorCode,
  LogCategory,
  LogLevel,
} from './utils/enhancedDebug'

// Backward compatibility imports
import {
  debugLog,
  logInitData,
  logAuthState,
  logTelegramEvent
} from './utils/debug'

// Layouts
import MainLayout from './components/Layout/MainLayout'

// Views
import EntrySelection from './views/EntrySelection'
import Dashboard from './views/Dashboard'
import Help from './views/Help'
import AdminDashboard from './views/AdminDashboard/AdminDashboard'
import MemberProfile from './views/MemberView/MemberProfile'
import Modules from './views/AdminDashboard/Modules'
import Members from './views/AdminDashboard/Members'
import Analytics from './views/AdminDashboard/Analytics'
import Scheduler from './views/AdminDashboard/Scheduler'
import Settings from './views/AdminDashboard/Settings'
import Economy from './views/AdminDashboard/Economy'
import BotBuilder from './views/AdminDashboard/BotBuilder'
import AdvancedFeatures from './views/AdminDashboard/AdvancedFeatures'
import ModerationQueue from './views/AdminDashboard/ModerationQueue'
import NotesAndFilters from './views/AdminDashboard/NotesAndFilters'
import Locks from './views/AdminDashboard/Locks'
import AntiSpam from './views/AdminDashboard/AntiSpam'
import RulesAndGreetings from './views/AdminDashboard/RulesAndGreetings'
import ImportExport from './views/AdminDashboard/ImportExport'
import CustomBotToken from './views/AdminDashboard/CustomBotToken'
import PollsCenter from './views/AdminDashboard/PollsCenter'
import SecurityCenter from './views/AdminDashboard/SecurityCenter'
import Loading from './components/UI/Loading'
import Integrations from './views/AdminDashboard/Integrations'
import GamificationHub from './views/AdminDashboard/GamificationHub'
import CommunityHub from './views/AdminDashboard/CommunityHub'
import GamesHub from './views/AdminDashboard/GamesHub'
import BroadcastCenter from './views/AdminDashboard/BroadcastCenter'
import AutomationCenter from './views/AdminDashboard/AutomationCenter'
import FormattingTools from './views/AdminDashboard/FormattingTools'
import AdvancedSearch from './views/AdminDashboard/AdvancedSearch'
import Graveyard from './views/AdminDashboard/Graveyard'

// New Intelligence Views
import GroupIntelligence from './views/AdminDashboard/GroupIntelligence'
import AutomationCenterEnhanced from './views/AdminDashboard/AutomationCenterEnhanced'

// App initialization stages
type AppStage = 
  | 'initializing'      // Initial load, checking Telegram context
  | 'entry-selection'   // Show entry selection (private chat or new user)
  | 'authenticating'    // Auth in progress
  | 'authenticated'     // Auth successful
  | 'error'             // Auth error

type EntryMethod = 'existing-groups' | 'custom-token' | 'first-time' | null

function App() {
  const { isAuthenticated, isLoading, isRehydrated, error, setAuth, setLoading, setError } = useAuthStore()
  const { currentGroup, setCurrentGroup } = useGroupStore()
  
  // App state
  const [stage, setStage] = useState<AppStage>('initializing')
  const [initData, setInitData] = useState<string>('')
  const [errorDetail, setErrorDetail] = useState<string>('')
  const [dbGroupId, setDbGroupId] = useState<number | null>(null)
  const [entryMethod, setEntryMethod] = useState<EntryMethod>(null)
  const [customBotToken, setCustomBotToken] = useState<string | null>(null)

  // Authentication function - can be called with or without custom token
  const authenticate = useCallback(async (botToken?: string) => {
    if (!initData) {
      setError('No Telegram Data')
      setErrorDetail('Authentication requires Telegram initData. Please open from Telegram.')
      setStage('error')
      return
    }

    setStage('authenticating')
    setLoading(true)
    setError(null)

    try {
      enhancedDebug.info('Starting authentication', LogCategory.AUTH, {
        hasCustomToken: !!botToken,
        initDataLength: initData.length,
      })

      // Authenticate with backend, optionally passing custom bot token
      const authData = await telegramAuth(initData, botToken)

      enhancedDebug.success('Authentication successful!', LogCategory.AUTH, {
        userId: authData.user?.id,
        username: authData.user?.username,
      })

      setAuth(authData.access_token, authData.user)

      // Try to resolve group from initData
      const tg = (window as any).Telegram?.WebApp
      const startParam = tg?.initDataUnsafe?.start_param
      const chatId = tg?.initDataUnsafe?.chat?.id
      const telegramChatId = startParam ? Number(startParam) : (chatId ? Number(chatId) : null)

      if (telegramChatId) {
        try {
          const group = await getGroupByTelegramId(telegramChatId)
          setDbGroupId(group.id)
          setCurrentGroup(group)
          enhancedDebug.success(`Resolved to Database Group ID: ${group.id}`, LogCategory.GROUPS)
        } catch (e: any) {
          enhancedDebug.warn('Failed to resolve Telegram Chat ID', LogCategory.GROUPS, { telegramChatId })
          // Don't fail auth, just continue without group resolution
        }
      }

      setStage('authenticated')
    } catch (err: any) {
      const errorAnalysis = ErrorAnalyzer.analyze(err, { initDataLength: initData.length })
      enhancedDebug.error('Authentication failed', err, LogCategory.AUTH, {
        responseData: err.response?.data,
        status: err.response?.status,
      })

      const detail = err.response?.data?.detail || 'Authentication failed'
      
      // Check if error indicates we need entry selection
      const needsEntrySelection = 
        detail.includes('not currently a member of any groups') ||
        detail.includes('Hash mismatch') ||
        detail.includes('Chat ID not found')

      if (needsEntrySelection && !botToken) {
        // Show entry selection instead of error
        setStage('entry-selection')
        setErrorDetail(detail)
        setLoading(false)
        return
      }

      setError('Authentication Failed')
      setErrorDetail(`${detail}\n\n${errorAnalysis.fix}`)
      setStage('error')
    } finally {
      setLoading(false)
    }
  }, [initData, setAuth, setLoading, setError, setCurrentGroup])

  // Initialize app - detect Telegram context
  useEffect(() => {
    const init = async () => {
      await enhancedDebug.withContext('App Initialization', LogCategory.INIT, async (ctx) => {
        ctx.log('Starting app initialization')
        setLoading(true)

        const tg = (window as any).Telegram?.WebApp
        telegramDebug.logInitData((window as any).Telegram)

        // Configure Telegram WebApp theme
        if (tg) {
          const version = parseFloat(tg.version || '6.0')
          if (version >= 6.1) {
            try {
              tg.setHeaderColor('#020617')
              tg.setBottomBarColor('#020617')
              tg.setBackgroundColor('#020617')
            } catch (e) {
              enhancedDebug.warn('Color settings not supported', LogCategory.TELEGRAM, e)
            }
          }
          tg.expand()

          // Set up event listeners
          tg.onEvent('viewportChanged', (data: any) => {
            telegramDebug.logWebSocketEvent('viewportChanged', data)
          })
          tg.onEvent('themeChanged', () => {
            telegramDebug.logWebSocketEvent('themeChanged', { colorScheme: tg.colorScheme })
          })
        }

        // Wait for initData
        let initDataRaw = tg?.initData || ''
        let attempts = 0
        const maxAttempts = 20

        while (!initDataRaw && tg && attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 100))
          initDataRaw = tg?.initData || ''
          attempts++
        }

        setInitData(initDataRaw)

        // Check for stored token - if exists, try to use it
        const storedToken = localStorage.getItem('nexus_token')
        
        if (storedToken) {
          enhancedDebug.info('Found stored token, checking validity')
          
          // If we have initData, try to re-authenticate to get fresh permissions
          if (initDataRaw) {
            await authenticate()
            return
          }
          
          // No initData but have stored token - allow access (user can refresh data)
          enhancedDebug.info('No initData but have stored token, allowing access')
          setStage('authenticated')
          setLoading(false)
          return
        }

        // No stored token - determine what to show
        if (!initDataRaw) {
          // Not in Telegram context
          enhancedDebug.error('No initData available', new Error(ErrorCode.MISSING_INIT_DATA), LogCategory.AUTH)
          setStage('entry-selection')
          setErrorDetail('Open this Mini App from Telegram to authenticate')
          setLoading(false)
          return
        }

        // We have initData - check if this is a private chat
        const chatType = tg?.initDataUnsafe?.chat?.type
        const chatId = tg?.initDataUnsafe?.chat?.id

        if (chatType === 'private' || !chatId) {
          // Private chat - show entry selection
          enhancedDebug.info('Detected private chat, showing entry selection')
          setStage('entry-selection')
          setLoading(false)
          return
        }

        // Group chat - try automatic authentication
        enhancedDebug.info('Detected group chat, attempting automatic authentication')
        await authenticate()
      })
    }

    init()
  }, [authenticate, setLoading])

  // Handle entry selection
  const handleSelectExistingGroups = useCallback(async () => {
    setEntryMethod('existing-groups')
    // Try auth without custom token - backend will try user's group memberships
    await authenticate()
  }, [authenticate])

  const handleSelectCustomToken = useCallback(async (token: string) => {
    setEntryMethod('custom-token')
    setCustomBotToken(token)
    // Store token for future use
    localStorage.setItem('nexus_custom_bot_token', token)
    // Try auth with custom token
    await authenticate(token)
  }, [authenticate])

  const handleSelectFirstTime = useCallback(() => {
    setEntryMethod('first-time')
    // First-time users need guidance, stay on entry selection
  }, [])

  // Loading state
  if (isLoading && stage === 'initializing') {
    return <Loading />
  }

  // Entry Selection - show for private chats or when auth needs guidance
  if (stage === 'entry-selection') {
    return (
      <EntrySelection
        onSelectExistingGroups={handleSelectExistingGroups}
        onSelectCustomToken={handleSelectCustomToken}
        onSelectFirstTime={handleSelectFirstTime}
        isLoading={isLoading}
        error={error}
      />
    )
  }

  // Error state
  if (stage === 'error' || error) {
    const isGroupMembershipError = errorDetail?.includes('not currently a member of any groups')
    const isInitDataError = errorDetail?.includes('Chat ID not found in initData') ||
                            errorDetail?.includes('No Telegram authentication')

    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/20">
            <span className="text-3xl">🤖</span>
          </div>
          <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
          <p className="text-red-400 mb-4">{error}</p>

          {isGroupMembershipError ? (
            <div className="bg-dark-800 rounded-xl p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                You need to add the bot to a group before using the Mini App:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Add the bot to one of your groups</li>
                <li>Send any message in the group</li>
                <li>Open the Mini App from the group</li>
              </ol>
              <button
                onClick={() => setStage('entry-selection')}
                className="mt-4 w-full py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white text-sm transition-colors"
              >
                Back to Options
              </button>
            </div>
          ) : isInitDataError ? (
            <div className="bg-dark-800 rounded-xl p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                The Mini App works best when opened from a group:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Go to a group with the bot</li>
                <li>Click the menu button (⋮ or ⋯)</li>
                <li>Select &quot;Mini App&quot; or &quot;🚀 Mini App&quot;</li>
              </ol>
              <button
                onClick={() => setStage('entry-selection')}
                className="mt-4 w-full py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white text-sm transition-colors"
              >
                Back to Options
              </button>
            </div>
          ) : errorDetail ? (
            <div className="bg-dark-800 rounded-xl p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">Error details:</p>
              <pre className="text-dark-400 text-xs font-mono whitespace-pre-wrap">{errorDetail}</pre>
            </div>
          ) : null}

          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
          >
            Retry
          </button>

          {import.meta.env.DEV && (
            <button
              onClick={() => {
                const report = enhancedDebug.generateReport()
                console.log(report)
                alert('Debug report printed to console')
              }}
              className="mt-4 ml-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              Debug Report
            </button>
          )}
        </div>
      </div>
    )
  }

  // Authenticated - show main app
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={
          isAuthenticated ? (
            dbGroupId ? <Navigate to={`/admin/${dbGroupId}`} /> : <Dashboard />
          ) : (
            <Navigate to="/" replace />
          )
        } />
        <Route path="/help" element={<Help />} />
        <Route path="/profile/:groupId" element={<MemberProfile />} />

        {/* Admin Dashboard Routes - All use Database Group ID */}
        <Route path="/admin/:groupId" element={<AdminDashboard />} />
        <Route path="/admin/:groupId/modules" element={<Modules />} />
        <Route path="/admin/:groupId/members" element={<Members />} />
        <Route path="/admin/:groupId/analytics" element={<Analytics />} />
        <Route path="/admin/:groupId/scheduler" element={<Scheduler />} />
        <Route path="/admin/:groupId/economy" element={<Economy />} />
        <Route path="/admin/:groupId/settings" element={<Settings />} />
        <Route path="/admin/:groupId/bot-builder" element={<BotBuilder />} />
        <Route path="/admin/:groupId/advanced" element={<AdvancedFeatures />} />

        {/* Feature Routes */}
        <Route path="/admin/:groupId/moderation" element={<ModerationQueue />} />
        <Route path="/admin/:groupId/notes-filters" element={<NotesAndFilters />} />
        <Route path="/admin/:groupId/locks" element={<Locks />} />
        <Route path="/admin/:groupId/antispam" element={<AntiSpam />} />
        <Route path="/admin/:groupId/rules-greetings" element={<RulesAndGreetings />} />
        <Route path="/admin/:groupId/import-export" element={<ImportExport />} />
        <Route path="/admin/:groupId/custom-bot" element={<CustomBotToken />} />
        <Route path="/admin/:groupId/integrations" element={<Integrations />} />

        {/* Unified Routes */}
        <Route path="/admin/:groupId/security" element={<SecurityCenter />} />
        <Route path="/admin/:groupId/polls" element={<PollsCenter />} />

        {/* Hubs - High Priority */}
        <Route path="/admin/:groupId/gamification" element={<GamificationHub />} />
        <Route path="/admin/:groupId/community" element={<CommunityHub />} />
        <Route path="/admin/:groupId/games" element={<GamesHub />} />

        {/* Hubs - Medium Priority */}
        <Route path="/admin/:groupId/broadcast" element={<BroadcastCenter />} />
        <Route path="/admin/:groupId/automation" element={<AutomationCenter />} />

        {/* Hubs - Low Priority */}
        <Route path="/admin/:groupId/formatting" element={<FormattingTools />} />
        <Route path="/admin/:groupId/search" element={<AdvancedSearch />} />

        {/* Message Graveyard */}
        <Route path="/admin/:groupId/graveyard" element={<Graveyard />} />

        {/* Group Intelligence */}
        <Route path="/admin/:groupId/intelligence" element={<GroupIntelligence />} />
        <Route path="/admin/:groupId/automation-enhanced" element={<AutomationCenterEnhanced />} />
      </Routes>
    </MainLayout>
  )
}

export default App
