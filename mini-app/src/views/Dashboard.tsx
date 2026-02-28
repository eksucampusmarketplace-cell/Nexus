import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Users, Settings, BarChart3 } from 'lucide-react'
import { useGroupStore } from '../stores/groupStore'
import { useAuthStore } from '../stores/authStore'
import { listGroups } from '../api/groups'
import Card from '../components/UI/Card'
import Loading from '../components/UI/Loading'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const navigate = useNavigate()
  const { groups, setGroups, isLoading, setLoading } = useGroupStore()
  const { user } = useAuthStore()

  useEffect(() => {
    const loadGroups = async () => {
      setLoading(true)
      try {
        const data = await listGroups()
        setGroups(data)
      } catch (error) {
        toast.error('Failed to load groups')
      } finally {
        setLoading(false)
      }
    }

    loadGroups()
  }, [])

  if (isLoading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Your Groups</h1>
        <p className="text-dark-400 mt-1">
          Select a group to manage
        </p>
      </div>

      {groups.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-dark-800 rounded-full flex items-center justify-center">
            <Shield className="w-8 h-8 text-dark-500" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No groups yet</h3>
          <p className="text-dark-400 max-w-sm mx-auto">
            Add the Nexus bot to your Telegram group to get started with advanced management features.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {groups.map((group) => (
            <Card
              key={group.id}
              onClick={() => navigate(`/admin/${group.id}`)}
              className="hover:bg-dark-800 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl flex items-center justify-center text-xl font-bold text-white">
                  {group.title.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-white">{group.title}</h3>
                  <div className="flex items-center gap-4 mt-1 text-sm text-dark-400">
                    <span className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      {group.member_count.toLocaleString()} members
                    </span>
                    {group.is_premium && (
                      <span className="text-yellow-500">Premium</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                    <Settings className="w-5 h-5 text-dark-400" />
                  </button>
                  <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                    <BarChart3 className="w-5 h-5 text-dark-400" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
