import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'
import { getGroupByTelegramId, getGroupStatsByTelegramId } from './api/groups'
import { 
  debugLog, 
  LogCategory, 
  LogLevel,
  logInitData, 
  logAuthState,
  logTelegramEvent 
} from './utils/debug'

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
      debugLog(LogCategory.INIT, '=== APP INITIALIZATION START ===', null);
      setLoading(true)
      logAuthState('initializing');

      // Get Telegram init data
      const tg = (window as any).Telegram?.WebApp
      
      // Log Telegram WebApp object
      debugLog(LogCategory.TELEGRAM, 'Telegram WebApp object:', tg ? 'Found' : 'NOT FOUND', tg ? LogLevel.INFO : LogLevel.ERROR);
      
      // Full init data dump
      logInitData(tg);

      // Configure Telegram WebApp theme to match our dark theme
      if (tg) {
        // Version check: color functions require WebApp 6.1+
        const version = parseFloat(tg.version || '6.0')
        debugLog(LogCategory.TELEGRAM, `WebApp version: ${version}`, null);
        
        if (version >= 6.1) {
          try {
            // Set header color to match our dark background
            tg.setHeaderColor('#020617')
            // Set bottom bar color to match our dark background
            tg.setBottomBarColor('#020617')
            // Set background color for the main content area
            tg.setBackgroundColor('#020617')
            debugLog(LogCategory.TELEGRAM, 'Theme colors set successfully', null);
          } catch (e) {
            debugLog(LogCategory.TELEGRAM, 'Color settings not supported', e, LogLevel.WARN);
          }
        } else {
          // For older versions, try color_key syntax
          try {
            tg.setHeaderColor({ color_key: 'bg_color' })
            debugLog(LogCategory.TELEGRAM, 'Header color set via color_key', null);
          } catch (e) {
            debugLog(LogCategory.TELEGRAM, 'Header color not supported in version', tg.version, LogLevel.WARN);
          }
        }
        // Expand the web app to full height
        debugLog(LogCategory.TELEGRAM, 'Calling tg.expand()', null);
        tg.expand()
        
        // Set up event listeners for Telegram events
        tg.onEvent('viewportChanged', (data: any) => {
          logTelegramEvent('viewportChanged', data);
        });
        tg.onEvent('themeChanged', () => {
          logTelegramEvent('themeChanged', { colorScheme: tg.colorScheme });
        });
      }

      // Wait for initData to be available (it can take a moment in private chats)
      let initDataRaw = tg?.initData || ''
      let attempts = 0
      const maxAttempts = 20 // Wait up to 2 seconds

      debugLog(LogCategory.INIT, `Starting initData wait loop. Initial value: ${initDataRaw ? 'Present' : 'Empty'}`, null);

      while (!initDataRaw && tg && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100))
        initDataRaw = tg?.initData || ''
        attempts++
        if (initDataRaw) {
          debugLog(LogCategory.INIT, `initData became available after ${attempts} attempts`, null);
          logInitData(tg);
        }
      }

      debugLog(LogCategory.INIT, `Wait loop complete. attempts=${attempts}, hasInitData=${!!initDataRaw}`, null);
      setInitData(initDataRaw)

      if (!initDataRaw) {
        // Not running in Telegram context or initData not available
        debugLog(LogCategory.INIT, 'No initData available after waiting', null, LogLevel.WARN);

        // Check if we have a stored token from previous session
        const storedToken = localStorage.getItem('nexus_token')
        debugLog(LogCategory.TOKEN, 'Checking for stored token:', storedToken ? 'Found' : 'Not found');
        
        if (storedToken) {
          debugLog(LogCategory.AUTH, 'Found stored token, allowing access with existing session', null);
          logAuthState('restored_from_storage');
          setAuthAttempted(true)
          setLoading(false)
          return
        }

        debugLog(LogCategory.AUTH, 'Not in Telegram context and no stored token', null, LogLevel.ERROR);
        logAuthState('no_auth_available');
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

      debugLog(LogCategory.GROUPS, `Extracted IDs - startParam: ${startParam}, chatId: ${chatId}, telegramChatId: ${telegramChatId}`, null);

      // No more localStorage! Backend handles bot token lookup based on user membership
      // The bot knows which groups the user is in and finds the right token automatically

      try {
        // Authenticate with backend
        // Backend finds bots based on user's group memberships (database-driven)
        debugLog(LogCategory.AUTH, 'Starting authentication with backend...', null);
        logAuthState('authenticating');
        
        debugLog(LogCategory.AUTH, 'Init data being sent (first 200 chars):', initDataRaw.substring(0, 200));
        debugLog(LogCategory.HASH, 'initData hash from initDataUnsafe:', tg?.initDataUnsafe?.hash);
        
        const authData = await telegramAuth(initDataRaw)
        debugLog(LogCategory.AUTH, 'Authentication successful!', { userId: authData.user?.id, username: authData.user?.username });
        logAuthState('authenticated');
        
        debugLog(LogCategory.TOKEN, 'Received access token (first 30 chars):', authData.access_token?.substring(0, 30));
        setAuth(authData.access_token, authData.user)
        debugLog(LogCategory.AUTH, 'Auth state set in store', null);

        // If we have a Telegram Chat ID, resolve it to Database Group ID
        if (telegramChatId) {
          try {
            debugLog(LogCategory.GROUPS, `Resolving Telegram Chat ID ${telegramChatId} to Database Group ID...`, null);
            const group = await getGroupByTelegramId(telegramChatId)
            setDbGroupId(group.id)
            setCurrentGroup(group)
            debugLog(LogCategory.GROUPS, `Resolved to Database Group ID: ${group.id}`, { groupTitle: group.title });
          } catch (e: any) {
            debugLog(LogCategory.GROUPS, 'Failed to resolve Telegram Chat ID:', e?.response?.data || e.message, LogLevel.ERROR);
            // Don't fail auth, just log it - user may need to add bot to group
          }
        } else {
          debugLog(LogCategory.GROUPS, 'No telegramChatId available, skipping group resolution', null);
        }
      } catch (err: any) {
        debugLog(LogCategory.AUTH, 'Authentication error:', err, LogLevel.ERROR);
        debugLog(LogCategory.AUTH, 'Error response data:', err.response?.data, LogLevel.ERROR);
        logAuthState('failed', { detail: err.response?.data?.detail });
        
        const detail = err.response?.data?.detail || 'Authentication failed'
        setError('Authentication Failed')
        setErrorDetail(detail)
      }

      setAuthAttempted(true)
      setLoading(false)
      debugLog(LogCategory.INIT, '=== APP INITIALIZATION COMPLETE ===', { authAttempted: true, isLoading: false });
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
