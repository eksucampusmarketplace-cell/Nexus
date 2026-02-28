import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, Users, MessageSquare, Gamepad2, Sparkles, Zap,
  Lock, Bell, Clock, Coins, Trophy, Settings, ChevronRight,
  ToggleLeft, ToggleRight, Info, AlertCircle, Check, X
} from 'lucide-react'
import { toggleApi, ModuleToggle, FeatureToggle } from '../api/toggles'
import toast from 'react-hot-toast'

interface ModuleToggleManagerProps {
  groupId: number
  onModuleToggle?: (moduleName: string, enabled: boolean) => void
}

// Module icons mapping
const moduleIcons: Record<string, any> = {
  moderation: Shield,
  welcome: MessageSquare,
  captcha: Lock,
  locks: Lock,
  antispam: Zap,
  economy: Coins,
  games: Gamepad2,
  reputation: Trophy,
  notes: MessageSquare,
  filters: MessageSquare,
  rules: MessageSquare,
  scheduler: Clock,
  ai_assistant: Sparkles,
  community: Users,
  identity: Users,
  analytics: Settings,
}

// Category icons
const categoryIcons: Record<string, any> = {
  moderation: Shield,
  greetings: Bell,
  antispam: Zap,
  community: Users,
  ai: Sparkles,
  games: Gamepad2,
  utility: Settings,
  integration: Settings,
}

export default function ModuleToggleManager({ groupId, onModuleToggle }: ModuleToggleManagerProps) {
  const [modules, setModules] = useState<ModuleToggle[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedModule, setExpandedModule] = useState<string | null>(null)
  const [saving, setSaving] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState<string | null>(null)

  useEffect(() => {
    loadModules()
  }, [groupId])

  const loadModules = async () => {
    try {
      setLoading(true)
      const data = await toggleApi.getModules(groupId)
      setModules(data)
    } catch (error) {
      console.error('Failed to load modules:', error)
      toast.error('Failed to load modules')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleModule = async (moduleName: string, enabled: boolean) => {
    setSaving(moduleName)
    try {
      await toggleApi.toggleModule(groupId, moduleName, enabled)
      setModules(prev => prev.map(m => 
        m.name === moduleName ? { ...m, enabled } : m
      ))
      toast.success(`${moduleName} ${enabled ? 'enabled' : 'disabled'}`)
      onModuleToggle?.(moduleName, enabled)
    } catch (error) {
      console.error('Failed to toggle module:', error)
      toast.error('Failed to update module')
    } finally {
      setSaving(null)
    }
  }

  const handleUpdateFeature = async (moduleName: string, featureKey: string, value: any) => {
    setSaving(`${moduleName}-${featureKey}`)
    try {
      await toggleApi.updateFeature(groupId, moduleName, featureKey, value)
      setModules(prev => prev.map(m => {
        if (m.name !== moduleName) return m
        return {
          ...m,
          features: m.features.map(f => 
            f.key === featureKey ? { ...f, value } : f
          )
        }
      }))
      toast.success('Setting updated')
    } catch (error) {
      console.error('Failed to update feature:', error)
      toast.error('Failed to update setting')
    } finally {
      setSaving(null)
    }
  }

  const handleResetModule = async (moduleName: string) => {
    if (!confirm(`Reset ${moduleName} to default settings?`)) return
    
    setSaving(moduleName)
    try {
      await toggleApi.resetModule(groupId, moduleName)
      await loadModules()
      toast.success('Module reset to defaults')
    } catch (error) {
      console.error('Failed to reset module:', error)
      toast.error('Failed to reset module')
    } finally {
      setSaving(null)
    }
  }

  // Group modules by category
  const groupedModules = modules.reduce((acc, module) => {
    const category = module.category || 'utility'
    if (!acc[category]) acc[category] = []
    acc[category].push(module)
    return acc
  }, {} as Record<string, ModuleToggle[]>)

  // Filter modules
  const filteredCategories = Object.entries(groupedModules).map(([category, mods]) => ({
    category,
    modules: mods.filter(m => 
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(c => c.modules.length > 0 && (!filterCategory || c.category === filterCategory))

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search modules..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-400 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors"
          />
          <Settings className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
        </div>
        
        <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
          <button
            onClick={() => setFilterCategory(null)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
              !filterCategory ? 'bg-primary-600 text-white' : 'bg-dark-800 text-dark-300 hover:text-white'
            }`}
          >
            All
          </button>
          {Object.keys(categoryIcons).map(category => (
            <button
              key={category}
              onClick={() => setFilterCategory(category)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                filterCategory === category ? 'bg-primary-600 text-white' : 'bg-dark-800 text-dark-300 hover:text-white'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Module Categories */}
      <div className="space-y-8">
        {filteredCategories.map(({ category, modules: categoryModules }) => (
          <div key={category}>
            <div className="flex items-center gap-2 mb-4">
              {(() => {
                const Icon = categoryIcons[category] || Settings
                return <Icon className="w-5 h-5 text-primary-500" />
              })()}
              <h3 className="text-lg font-semibold text-white">
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </h3>
              <span className="px-2 py-0.5 bg-dark-800 rounded text-sm text-dark-400">
                {categoryModules.length}
              </span>
            </div>

            <div className="grid gap-4">
              {categoryModules.map(module => (
                <ModuleCard
                  key={module.name}
                  module={module}
                  isExpanded={expandedModule === module.name}
                  saving={saving}
                  onToggle={() => handleToggleModule(module.name, !module.enabled)}
                  onExpand={() => setExpandedModule(expandedModule === module.name ? null : module.name)}
                  onUpdateFeature={(key, value) => handleUpdateFeature(module.name, key, value)}
                  onReset={() => handleResetModule(module.name)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredCategories.length === 0 && (
        <div className="text-center py-12">
          <Settings className="w-12 h-12 text-dark-600 mx-auto mb-4" />
          <p className="text-dark-400">No modules found matching your search</p>
        </div>
      )}
    </div>
  )
}

// Module Card Component
function ModuleCard({
  module,
  isExpanded,
  saving,
  onToggle,
  onExpand,
  onUpdateFeature,
  onReset,
}: {
  module: ModuleToggle
  isExpanded: boolean
  saving: string | null
  onToggle: () => void
  onExpand: () => void
  onUpdateFeature: (key: string, value: any) => void
  onReset: () => void
}) {
  const Icon = moduleIcons[module.name] || Settings
  const isSaving = saving === module.name

  return (
    <motion.div
      layout
      className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden"
    >
      <div
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-dark-750 transition-colors"
        onClick={onExpand}
      >
        {/* Module Icon */}
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
          module.enabled ? 'bg-primary-600/20 text-primary-500' : 'bg-dark-700 text-dark-400'
        }`}>
          <Icon className="w-6 h-6" />
        </div>

        {/* Module Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-white truncate">
              {module.displayName || module.name}
            </h4>
            {module.enabled && (
              <span className="px-2 py-0.5 bg-green-600/20 text-green-400 text-xs rounded-full">
                Active
              </span>
            )}
          </div>
          <p className="text-sm text-dark-400 truncate">{module.description}</p>
        </div>

        {/* Toggle */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggle()
          }}
          disabled={isSaving}
          className={`p-2 rounded-lg transition-colors ${
            isSaving ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {module.enabled ? (
            <ToggleRight className="w-8 h-8 text-primary-500" />
          ) : (
            <ToggleLeft className="w-8 h-8 text-dark-400" />
          )}
        </button>

        {/* Expand Arrow */}
        <motion.div
          animate={{ rotate: isExpanded ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="w-5 h-5 text-dark-400" />
        </motion.div>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="border-t border-dark-700 p-4 space-y-4">
              {/* Module Configuration */}
              {module.features.length > 0 ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-medium text-dark-300">Configuration</h5>
                    <button
                      onClick={onReset}
                      className="text-xs text-dark-400 hover:text-white transition-colors"
                    >
                      Reset to defaults
                    </button>
                  </div>
                  
                  {module.features.map(feature => (
                    <FeatureInput
                      key={feature.key}
                      feature={feature}
                      disabled={!module.enabled}
                      saving={saving === `${module.name}-${feature.key}`}
                      onChange={(value) => onUpdateFeature(feature.key, value)}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-dark-400">
                  No additional configuration for this module.
                </p>
              )}

              {/* Quick Info */}
              <div className="flex items-start gap-2 p-3 bg-dark-850 rounded-lg">
                <Info className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-dark-400">
                  {module.enabled 
                    ? `This module is active. Changes will take effect immediately.`
                    : `Enable this module to start using its features.`}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// Feature Input Component
function FeatureInput({
  feature,
  disabled,
  saving,
  onChange,
}: {
  feature: FeatureToggle
  disabled: boolean
  saving: boolean
  onChange: (value: any) => void
}) {
  const [localValue, setLocalValue] = useState(feature.value)

  useEffect(() => {
    setLocalValue(feature.value)
  }, [feature.value])

  const handleChange = (value: any) => {
    setLocalValue(value)
    onChange(value)
  }

  const renderInput = () => {
    switch (feature.type) {
      case 'boolean':
        return (
          <button
            onClick={() => !disabled && handleChange(!localValue)}
            disabled={disabled || saving}
            className={`flex items-center gap-2 ${
              disabled ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {localValue ? (
              <>
                <ToggleRight className="w-6 h-6 text-primary-500" />
                <span className="text-sm text-primary-400">Enabled</span>
              </>
            ) : (
              <>
                <ToggleLeft className="w-6 h-6 text-dark-400" />
                <span className="text-sm text-dark-400">Disabled</span>
              </>
            )}
          </button>
        )

      case 'select':
        return (
          <select
            value={localValue}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled || saving}
            className="w-full px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
          >
            {feature.options?.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )

      case 'number':
        return (
          <input
            type="number"
            value={localValue}
            onChange={(e) => handleChange(parseInt(e.target.value))}
            disabled={disabled || saving}
            min={feature.min}
            max={feature.max}
            className="w-full px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
          />
        )

      case 'duration':
        return (
          <div className="flex gap-2">
            <input
              type="number"
              value={parseInt(localValue) || 0}
              onChange={(e) => handleChange(e.target.value + 'h')}
              disabled={disabled || saving}
              className="flex-1 px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
            />
            <select
              value={localValue?.toString().slice(-1) || 'h'}
              onChange={(e) => {
                const num = parseInt(localValue) || 1
                handleChange(num + e.target.value)
              }}
              disabled={disabled || saving}
              className="px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
            >
              <option value="m">Minutes</option>
              <option value="h">Hours</option>
              <option value="d">Days</option>
              <option value="w">Weeks</option>
            </select>
          </div>
        )

      case 'text':
        return (
          <input
            type="text"
            value={localValue}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled || saving}
            placeholder={feature.placeholder}
            className="w-full px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
          />
        )

      default:
        return (
          <input
            type="text"
            value={localValue}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled || saving}
            className="w-full px-3 py-2 bg-dark-850 border border-dark-700 rounded-lg text-white text-sm focus:border-primary-500 outline-none disabled:opacity-50"
          />
        )
    }
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <div className="flex-1 min-w-0">
        <label className="text-sm text-dark-300">{feature.label}</label>
        {feature.description && (
          <p className="text-xs text-dark-500">{feature.description}</p>
        )}
      </div>
      <div className="w-full sm:w-auto sm:min-w-[200px]">
        {renderInput()}
      </div>
      {saving && (
        <div className="animate-spin w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full" />
      )}
    </div>
  )
}
