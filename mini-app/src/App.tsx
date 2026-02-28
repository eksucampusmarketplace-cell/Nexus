import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useGroupStore } from './stores/groupStore'
import { telegramAuth } from './api/auth'

// Layouts
import MainLayout from './components/Layout/MainLayout'

// Views
import Dashboard from './views/Dashboard'
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
import Loading from './components/UI/Loading'

function App() {
  const { isAuthenticated, isLoading, error, setAuth, setLoading } = useAuthStore()
  const { currentGroup, setCurrentGroup } = useGroupStore()
  const [initData, setInitData] = useState<string>('')

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      
      // Get Telegram init data
      const tg = (window as any).Telegram?.WebApp
      const initDataRaw = tg?.initData || ''
      setInitData(initDataRaw)

      if (initDataRaw) {
        try {
          // Authenticate with backend
          const authData = await telegramAuth(initDataRaw)
          setAuth(authData.access_token, authData.user)
        } catch (err) {
          console.error('Auth error:', err)
        }
      }

      setLoading(false)
    }

    init()
  }, [])

  if (isLoading) {
    return <Loading />
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
        <Route path="/profile/:groupId" element={<MemberProfile />} />
        <Route path="/admin/:groupId" element={<AdminDashboard />} />
        <Route path="/admin/:groupId/modules" element={<Modules />} />
        <Route path="/admin/:groupId/members" element={<Members />} />
        <Route path="/admin/:groupId/analytics" element={<Analytics />} />
        <Route path="/admin/:groupId/scheduler" element={<Scheduler />} />
        <Route path="/admin/:groupId/economy" element={<Economy />} />
        <Route path="/admin/:groupId/settings" element={<Settings />} />
        <Route path="/admin/:groupId/bot-builder" element={<BotBuilder />} />
        <Route path="/admin/:groupId/advanced" element={<AdvancedFeatures />} />
      </Routes>
    </MainLayout>
  )
}

export default App
