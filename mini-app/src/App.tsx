import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'

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
  const { isAuthenticated, isLoading, error, setAuth, setLoading, setError } = useAuthStore()
  const { currentGroup, setCurrentGroup } = useGroupStore()
  const [initData, setInitData] = useState<string>('')
  const [errorDetail, setErrorDetail] = useState<string>('')

  useEffect(() => {
    const init = async () => {
      setLoading(true)

      // Get Telegram init data
      const tg = (window as any).Telegram?.WebApp
      const initDataRaw = tg?.initData || ''
      setInitData(initDataRaw)

      if (!initDataRaw) {
        // Not running in Telegram context
        console.log('Not running in Telegram WebApp context')
        setLoading(false)
        return
      }

      // Get group ID from start_param or chat
      const startParam = tg?.initDataUnsafe?.start_param
      const chatId = tg?.initDataUnsafe?.chat?.id
      const groupId = startParam ? parseInt(startParam) : (chatId || null)

      // Try to get custom bot token from localStorage (optional - backend handles lookup now)
      let customBotToken: string | undefined
      if (groupId) {
        try {
          const storedTokens = JSON.parse(localStorage.getItem('nexus_custom_bot_tokens') || '{}')
          customBotToken = storedTokens[groupId]
        } catch (e) {
          console.warn('Failed to read custom bot tokens from localStorage:', e)
        }
      }

      try {
        // Authenticate with backend
        // Backend now handles bot token lookup automatically
        const authData = await telegramAuth(initDataRaw, customBotToken)
        setAuth(authData.access_token, authData.user)
      } catch (err: any) {
        console.error('Auth error:', err)
        const detail = err.response?.data?.detail || 'Authentication failed'
        setError('Authentication Failed')
        setErrorDetail(detail)
      }

      setLoading(false)
    }

    init()
  }, [setAuth, setLoading, setError])

  if (isLoading) {
    return <Loading />
  }

  // Show error if authentication failed
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md p-6">
          <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
          <p className="text-red-400 mb-2">{error}</p>
          {errorDetail && (
            <p className="text-dark-500 text-sm mb-4 font-mono text-xs break-all">{errorDetail}</p>
          )}
          <p className="text-dark-400 text-sm">Please try opening the Mini App again from Telegram.</p>
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
  const tg = (window as any).Telegram?.WebApp
  const startParam = tg?.initDataUnsafe?.start_param
  const groupId = startParam ? parseInt(startParam) : null
  
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={
          isAuthenticated ? (
            groupId ? <Navigate to={`/admin/${groupId}`} /> : <Dashboard />
          ) : (
            <div className="flex items-center justify-center h-screen">
              <div className="text-center">
                <h1 className="text-3xl font-bold mb-4 gradient-text">Nexus</h1>
                <p className="text-dark-400 mb-6">Open this Mini App from Telegram</p>
              </div>
            </div>
          )
        } />
        <Route path="/help" element={<Help />} />
        <Route path="/profile/:groupId" element={<MemberProfile />} />
        
        {/* Admin Dashboard Routes */}
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
