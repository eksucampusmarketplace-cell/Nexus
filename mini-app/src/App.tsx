import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'
import { getGroupByTelegramId, getGroupStatsByTelegramId } from './api/groups'

// Layouts
import MainLayout from './components/Layout/MainLayout'

// Views
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

function App() {
  const { isAuthenticated, isLoading, isRehydrated, error, setAuth, setLoading, setError } = useAuthStore()
  const { currentGroup, setCurrentGroup } = useGroupStore()
  const [initData, setInitData] = useState<string>('')
  const [errorDetail, setErrorDetail] = useState<string>('')
  const [authAttempted, setAuthAttempted] = useState(false)
  const [dbGroupId, setDbGroupId] = useState<number | null>(null) // Store the Database Group ID

  useEffect(() => {
    const init = async () => {
      setLoading(true)

      // Get Telegram init data
      const tg = (window as any).Telegram?.WebApp

      // Configure Telegram WebApp theme to match our dark theme
      if (tg) {
        // Version check: color functions require WebApp 6.1+
        const version = parseFloat(tg.version || '6.0')
        if (version >= 6.1) {
          try {
            // Set header color to match our dark background
            tg.setHeaderColor('#020617')
            // Set bottom bar color to match our dark background
            tg.setBottomBarColor('#020617')
            // Set background color for the main content area
            tg.setBackgroundColor('#020617')
          } catch (e) {
            console.log('[App] Color settings not supported')
          }
        } else {
          // For older versions, try color_key syntax
          try {
            tg.setHeaderColor({ color_key: 'bg_color' })
          } catch (e) {
            console.log('[App] Header color not supported in version', tg.version)
          }
        }
        // Expand the web app to full height
        tg.expand()
      }

      // Wait for initData to be available (it can take a moment in private chats)
      let initDataRaw = tg?.initData || ''
      let attempts = 0
      const maxAttempts = 20 // Wait up to 2 seconds

      while (!initDataRaw && tg && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100))
        initDataRaw = tg?.initData || ''
        attempts++
        if (initDataRaw) {
          console.log(`[App] initData became available after ${attempts} attempts`)
        }
      }

      setInitData(initDataRaw)

      if (!initDataRaw) {
        // Not running in Telegram context or initData not available
        console.log('[App] No initData available after waiting')

        // Check if we have a stored token from previous session
        const storedToken = localStorage.getItem('nexus_token')
        if (storedToken) {
          console.log('[App] Found stored token, allowing access with existing session')
          setAuthAttempted(true)
          setLoading(false)
          return
        }

        console.log('[App] Not in Telegram context and no stored token')
        setAuthAttempted(true)
        setLoading(false)
        return
      }

      // Get Telegram Chat ID from start_param or chat
      // IMPORTANT: Keep as string to avoid JavaScript number precision loss
      // Telegram IDs can exceed Number.MAX_SAFE_INTEGER (2^53-1)
      const startParam = tg?.initDataUnsafe?.start_param
      const chatId = tg?.initDataUnsafe?.chat?.id
      const groupIdStr = startParam ? String(startParam) : (chatId ? String(chatId) : null)
      const telegramChatId = groupIdStr ? Number(groupIdStr) : null

      // No more localStorage! Backend handles bot token lookup based on user membership
      // The bot knows which groups the user is in and finds the right token automatically

      try {
        // Authenticate with backend
        // Backend finds bots based on user's group memberships (database-driven)
        console.log('[App] Starting authentication...')
        console.log('[App] Backend will find bots based on your group memberships')
        const authData = await telegramAuth(initDataRaw)
        console.log('[App] Authentication successful, setting auth state')
        setAuth(authData.access_token, authData.user)
        console.log('[App] Auth state set')

        // If we have a Telegram Chat ID, resolve it to Database Group ID
        if (telegramChatId) {
          try {
            console.log('[App] Resolving Telegram Chat ID to Database Group ID:', telegramChatId)
            const group = await getGroupByTelegramId(telegramChatId)
            setDbGroupId(group.id)
            setCurrentGroup(group)
            console.log('[App] Resolved to Database Group ID:', group.id)
          } catch (e: any) {
            console.error('[App] Failed to resolve Telegram Chat ID:', e)
            // Don't fail auth, just log it - user may need to add bot to group
          }
        }
      } catch (err: any) {
        console.error('Auth error:', err)
        const detail = err.response?.data?.detail || 'Authentication failed'
        setError('Authentication Failed')
        setErrorDetail(detail)
      }

      setAuthAttempted(true)
      setLoading(false)
    }

    init()
  }, [setAuth, setLoading, setError])

  if (isLoading) {
    return <Loading />
  }

  // Show error if authentication failed
  if (error) {
    // Check if the error is about not being in any groups
    const isGroupMembershipError = errorDetail?.includes('not currently a member of any groups')
    const isInitDataError = errorDetail?.includes('Chat ID not found in initData')

    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md p-6">
          <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
          <p className="text-red-400 mb-2">{error}</p>

          {isGroupMembershipError ? (
            <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                You need to add the bot to a group before using the Mini App:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Add the bot to one of your groups</li>
                <li>Send any message in the group</li>
                <li>Open the Mini App from the group</li>
              </ol>
            </div>
          ) : isInitDataError ? (
            <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
              <p className="text-dark-300 text-sm mb-2">
                The Mini App works best when opened from a group:
              </p>
              <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                <li>Go to a group with the bot</li>
                <li>Click the menu button (⋮ or ⋯)</li>
                <li>Select "Mini App" or "🚀 Mini App"</li>
              </ol>
            </div>
          ) : errorDetail ? (
            <p className="text-dark-500 text-sm mb-4 font-mono text-xs break-all">{errorDetail}</p>
          ) : null}

          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Check if opened from a specific group
  // Use the resolved Database Group ID for navigation
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={
          isAuthenticated ? (
            dbGroupId ? <Navigate to={`/admin/${dbGroupId}`} /> : <Dashboard />
          ) : (
            <div className="flex items-center justify-center h-screen">
              <div className="text-center max-w-md p-6">
                <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
                <p className="text-dark-400 mb-4">Open this Mini App from Telegram</p>
                <div className="bg-dark-800 rounded-lg p-4 mb-4 text-left">
                  <p className="text-dark-300 text-sm mb-2">To use the Mini App:</p>
                  <ol className="text-dark-400 text-sm list-decimal list-inside space-y-1">
                    <li>Add the bot to a Telegram group</li>
                    <li>Send any message in the group</li>
                    <li>Open the Mini App from the group menu</li>
                  </ol>
                </div>
                <p className="text-dark-500 text-xs">Or check that your session hasn't expired</p>
              </div>
            </div>
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

        {/* New Feature Routes */}
        <Route path="/admin/:groupId/moderation" element={<ModerationQueue />} />
        <Route path="/admin/:groupId/notes-filters" element={<NotesAndFilters />} />
        <Route path="/admin/:groupId/locks" element={<Locks />} />
        <Route path="/admin/:groupId/antispam" element={<AntiSpam />} />
        <Route path="/admin/:groupId/rules-greetings" element={<RulesAndGreetings />} />
        <Route path="/admin/:groupId/import-export" element={<ImportExport />} />
        <Route path="/admin/:groupId/custom-bot" element={<CustomBotToken />} />
        <Route path="/admin/:groupId/integrations" element={<Integrations />} />

        {/* New Unified Routes */}
        <Route path="/admin/:groupId/security" element={<SecurityCenter />} />
        <Route path="/admin/:groupId/polls" element={<PollsCenter />} />

        {/* New Hubs - High Priority */}
        <Route path="/admin/:groupId/gamification" element={<GamificationHub />} />
        <Route path="/admin/:groupId/community" element={<CommunityHub />} />
        <Route path="/admin/:groupId/games" element={<GamesHub />} />

        {/* New Hubs - Medium Priority */}
        <Route path="/admin/:groupId/broadcast" element={<BroadcastCenter />} />
        <Route path="/admin/:groupId/automation" element={<AutomationCenter />} />

        {/* New Hubs - Low Priority */}
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
