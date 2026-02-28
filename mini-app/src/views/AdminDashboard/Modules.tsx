import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Shield,
  MessageSquare,
  Ban,
  Lock,
  FileText,
  Sparkles,
  Gamepad2,
  Wallet,
  BarChart3,
  Loader2,
} from 'lucide-react'
import { useModuleStore } from '../../stores/moduleStore'
import { listGroupModules, enableModule, disableModule } from '../../api/modules'
import Toggle from '../../components/UI/Toggle'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

const categoryIcons: Record<string, any> = {
  moderation: Shield,
  greetings: MessageSquare,
  antispam: Ban,
  utility: FileText,
  ai: Sparkles,
  games: Gamepad2,
  economy: Wallet,
  community: BarChart3,
}

const categoryColors: Record<string, string> = {
  moderation: 'text-red-500 bg-red-500/10',
  greetings: 'text-green-500 bg-green-500/10',
  antispam: 'text-orange-500 bg-orange-500/10',
  utility: 'text-blue-500 bg-blue-500/10',
  ai: 'text-purple-500 bg-purple-500/10',
  games: 'text-pink-500 bg-pink-500/10',
  economy: 'text-yellow-500 bg-yellow-500/10',
  community: 'text-cyan-500 bg-cyan-500/10',
}

export default function Modules() {
  const { groupId } = useParams<{ groupId: string }>()
  const { groupModules, setGroupModules, updateModuleStatus, isLoading, setLoading } = useModuleStore()
  const [toggling, setToggling] = useState<string | null>(null)

  const modules = groupId ? groupModules[parseInt(groupId)] || [] : []

  useEffect(() => {
    const loadModules = async () => {
      if (!groupId) return
      setLoading(true)
      try {
        const data = await listGroupModules(parseInt(groupId))
        setGroupModules(parseInt(groupId), data)
      } catch (error) {
        toast.error('Failed to load modules')
      } finally {
        setLoading(false)
      }
    }

    loadModules()
  }, [groupId])

  const handleToggle = async (moduleName: string, currentStatus: boolean) => {
    if (!groupId) return
    setToggling(moduleName)

    try {
      if (currentStatus) {
        await disableModule(parseInt(groupId), moduleName)
        updateModuleStatus(parseInt(groupId), moduleName, false)
        toast.success(`${moduleName} disabled`)
      } else {
        await enableModule(parseInt(groupId), moduleName)
        updateModuleStatus(parseInt(groupId), moduleName, true)
        toast.success(`${moduleName} enabled`)
      }
    } catch (error) {
      toast.error('Failed to update module')
    } finally {
      setToggling(null)
    }
  }

  if (isLoading) {
    return <Loading />
  }

  const groupedModules = modules.reduce((acc, module) => {
    if (!acc[module.category]) acc[module.category] = []
    acc[module.category].push(module)
    return acc
  }, {} as Record<string, typeof modules>)

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Modules</h1>
        <p className="text-dark-400 mt-1">
          Enable and configure bot modules for your group
        </p>
      </div>

      <div className="space-y-6">
        {Object.entries(groupedModules).map(([category, categoryModules]) => {
          const Icon = categoryIcons[category] || Shield
          return (
            <div key={category}>
              <div className="flex items-center gap-2 mb-3">
                <Icon className="w-5 h-5 text-dark-400" />
                <h2 className="text-sm font-semibold text-dark-300 uppercase tracking-wider">
                  {category}
                </h2>
              </div>

              <div className="space-y-3">
                {categoryModules.map((module) => (
                  <div
                    key={module.name}
                    className="bg-dark-900 rounded-xl border border-dark-800 p-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${categoryColors[module.category] || 'text-gray-500 bg-gray-500/10'}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold text-white capitalize">
                            {module.name.replace('_', ' ')}
                          </h3>
                          <div className="flex items-center gap-2">
                            {toggling === module.name && (
                              <Loader2 className="w-4 h-4 animate-spin text-dark-400" />
                            )}
                            <Toggle
                              checked={module.is_enabled}
                              onChange={() => handleToggle(module.name, module.is_enabled)}
                            />
                          </div>
                        </div>
                        <p className="text-sm text-dark-400 mt-1">
                          {module.description}
                        </p>

                        {module.is_enabled && module.commands.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-dark-800">
                            <p className="text-xs text-dark-500 mb-2">Available Commands:</p>
                            <div className="flex flex-wrap gap-2">
                              {module.commands.slice(0, 4).map((cmd) => (
                                <code
                                  key={cmd.name}
                                  className="text-xs bg-dark-800 px-2 py-1 rounded text-dark-300"
                                >
                                  /{cmd.name}
                                </code>
                              ))}
                              {module.commands.length > 4 && (
                                <span className="text-xs text-dark-500">
                                  +{module.commands.length - 4} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {module.dependencies.length > 0 && (
                          <div className="mt-2 text-xs text-dark-500">
                            Requires: {module.dependencies.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
