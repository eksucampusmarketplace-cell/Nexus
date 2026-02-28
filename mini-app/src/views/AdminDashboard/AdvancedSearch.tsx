import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Search,
  Filter,
  User,
  MessageSquare,
  Shield,
  FileText,
  Clock,
  Calendar,
  X,
  ChevronDown,
  ChevronUp,
  Download,
  History,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Ban,
  UserX,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import StatCard from '../../components/UI/StatCard'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as searchAPI from '../../api/search'

Modal.setAppElement('#root')

type TabType = 'search' | 'users' | 'moderation' | 'messages' | 'stats'
type SearchType = 'all' | 'messages' | 'users' | 'moderation' | 'notes'

export default function AdvancedSearch() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>('search')
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('all')
  const [results, setResults] = useState<searchAPI.SearchResult[]>([])
  const [userResults, setUserResults] = useState<searchAPI.UserSearchResult[]>([])
  const [moderationResults, setModerationResults] = useState<searchAPI.ModerationSearchResult[]>([])
  const [messageResults, setMessageResults] = useState<searchAPI.MessageSearchResult[]>([])
  const [stats, setStats] = useState<searchAPI.SearchStats | null>(null)
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)
  
  // Filters
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [selectedRole, setSelectedRole] = useState('')
  const [selectedAction, setSelectedAction] = useState('')

  useEffect(() => {
    if (groupId) {
      loadStats()
      loadRecentSearches()
    }
  }, [groupId])

  const loadStats = async () => {
    if (!groupId) return
    try {
      const res = await searchAPI.getSearchStats(parseInt(groupId))
      setStats(res)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const loadRecentSearches = async () => {
    if (!groupId) return
    try {
      const res = await searchAPI.getRecentSearches(parseInt(groupId))
      setRecentSearches(res)
    } catch (error) {
      console.error('Failed to load recent searches:', error)
    }
  }

  const handleSearch = async () => {
    if (!groupId || !query.trim()) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'search':
          const searchRes = await searchAPI.search(parseInt(groupId), {
            query,
            filters: {
              types: searchType === 'all' ? undefined : [searchType],
              date_from: dateFrom || undefined,
              date_to: dateTo || undefined,
            },
            sort_by: 'relevance',
            sort_order: 'desc',
            page: 1,
            page_size: 20
          })
          setResults(searchRes.results)
          break
        case 'users':
          const userRes = await searchAPI.searchUsers(parseInt(groupId), query, {
            role: selectedRole || undefined
          })
          setUserResults(userRes)
          break
        case 'moderation':
          const modRes = await searchAPI.searchModerations(parseInt(groupId), query, {
            action_type: selectedAction || undefined,
            date_from: dateFrom || undefined,
            date_to: dateTo || undefined,
          })
          setModerationResults(modRes)
          break
        case 'messages':
          const msgRes = await searchAPI.searchMessages(parseInt(groupId), query, {
            date_from: dateFrom || undefined,
            date_to: dateTo || undefined,
          })
          setMessageResults(msgRes)
          break
      }
    } catch (error) {
      console.error('Search failed:', error)
      toast.error('Search failed')
    } finally {
      setLoading(false)
    }
  }

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'message': return MessageSquare
      case 'user': return User
      case 'moderation': return Shield
      case 'note': return FileText
      case 'filter': return Filter
      default: return Search
    }
  }

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'warn': return AlertTriangle
      case 'mute': return Shield
      case 'ban': return Ban
      case 'kick': return UserX
      case 'unmute': return CheckCircle
      case 'unban': return CheckCircle
      default: return Shield
    }
  }

  const getActionColor = (actionType: string) => {
    switch (actionType) {
      case 'warn': return 'text-yellow-400'
      case 'mute': return 'text-orange-400'
      case 'ban': return 'text-red-400'
      case 'kick': return 'text-red-400'
      case 'unmute': return 'text-green-400'
      case 'unban': return 'text-green-400'
      default: return 'text-dark-400'
    }
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500/20 to-violet-500/20 rounded-xl flex items-center justify-center">
            <Search className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Advanced Search</h1>
            <p className="text-dark-400 mt-1">Search messages, users, moderation history</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'search', label: 'Universal Search', icon: Search },
          { id: 'users', label: 'Users', icon: User },
          { id: 'moderation', label: 'Moderation', icon: Shield },
          { id: 'messages', label: 'Messages', icon: MessageSquare },
          { id: 'stats', label: 'Stats', icon: BarChart3 },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id as TabType)
              setResults([])
              setUserResults([])
              setModerationResults([])
              setMessageResults([])
            }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      {activeTab !== 'stats' && (
        <Card className="mb-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search..."
                className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            {activeTab === 'search' && (
              <select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value as SearchType)}
                className="px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All</option>
                <option value="messages">Messages</option>
                <option value="users">Users</option>
                <option value="moderation">Moderation</option>
                <option value="notes">Notes</option>
              </select>
            )}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-3 rounded-xl transition-colors ${
                showFilters ? 'bg-indigo-500/20 text-indigo-400' : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
              }`}
            >
              <Filter className="w-5 h-5" />
            </button>
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl text-white font-medium transition-colors"
            >
              {loading ? '...' : 'Search'}
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-dark-800 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm text-dark-400 mb-1">From Date</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-sm text-dark-400 mb-1">To Date</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
                />
              </div>
              {activeTab === 'users' && (
                <div>
                  <label className="block text-sm text-dark-400 mb-1">Role</label>
                  <select
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
                  >
                    <option value="">All Roles</option>
                    <option value="owner">Owner</option>
                    <option value="admin">Admin</option>
                    <option value="mod">Moderator</option>
                    <option value="member">Member</option>
                  </select>
                </div>
              )}
              {activeTab === 'moderation' && (
                <div>
                  <label className="block text-sm text-dark-400 mb-1">Action</label>
                  <select
                    value={selectedAction}
                    onChange={(e) => setSelectedAction(e.target.value)}
                    className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white text-sm"
                  >
                    <option value="">All Actions</option>
                    <option value="warn">Warn</option>
                    <option value="mute">Mute</option>
                    <option value="ban">Ban</option>
                    <option value="kick">Kick</option>
                  </select>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Results */}
      {activeTab === 'search' && results.length > 0 && (
        <div className="space-y-3">
          <p className="text-dark-400 text-sm">{results.length} results found</p>
          {results.map((result, index) => {
            const Icon = getResultIcon(result.type)
            return (
              <Card key={index} className="hover:border-dark-700 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-dark-800 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 bg-dark-800 rounded text-xs text-dark-400 uppercase">
                        {result.type}
                      </span>
                      <span className="text-dark-500 text-xs">
                        {new Date(result.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h4 className="font-medium text-white">{result.title}</h4>
                    {result.content && (
                      <p className="text-dark-400 text-sm line-clamp-2 mt-1">{result.content}</p>
                    )}
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* User Results */}
      {activeTab === 'users' && userResults.length > 0 && (
        <div className="space-y-3">
          <p className="text-dark-400 text-sm">{userResults.length} users found</p>
          {userResults.map(user => (
            <Card key={user.id} className="hover:border-dark-700 transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-lg font-bold text-white">
                  {user.first_name.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-white">{user.first_name}</h4>
                    {user.username && (
                      <span className="text-dark-400 text-sm">@{user.username}</span>
                    )}
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      user.role === 'owner' ? 'bg-red-500/20 text-red-400' :
                      user.role === 'admin' ? 'bg-purple-500/20 text-purple-400' :
                      user.role === 'mod' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-dark-700 text-dark-400'
                    }`}>
                      {user.role}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-1 text-sm text-dark-400">
                    <span>Level {user.level}</span>
                    <span>{user.xp} XP</span>
                    <span>{user.message_count} messages</span>
                    {user.is_muted && <span className="text-orange-400">Muted</span>}
                    {user.is_banned && <span className="text-red-400">Banned</span>}
                    {user.warn_count > 0 && <span className="text-yellow-400">{user.warn_count} warnings</span>}
                  </div>
                </div>
                <span className="text-dark-500 text-sm">
                  Joined {new Date(user.joined_at).toLocaleDateString()}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Moderation Results */}
      {activeTab === 'moderation' && moderationResults.length > 0 && (
        <div className="space-y-3">
          <p className="text-dark-400 text-sm">{moderationResults.length} actions found</p>
          {moderationResults.map(action => {
            const Icon = getActionIcon(action.action_type)
            return (
              <Card key={action.id} className="hover:border-dark-700 transition-colors">
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    action.action_type.includes('un') ? 'bg-green-500/20' : 'bg-red-500/20'
                  }`}>
                    <Icon className={`w-5 h-5 ${getActionColor(action.action_type)}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs uppercase ${getActionColor(action.action_type)}`}>
                        {action.action_type}
                      </span>
                      {action.duration && (
                        <span className="text-dark-400 text-sm">for {action.duration}</span>
                      )}
                    </div>
                    <p className="text-white">
                      <span className="text-indigo-400">{action.target_user.first_name}</span>
                      {' '}was {action.action_type}d by{' '}
                      <span className="text-indigo-400">{action.actor.first_name}</span>
                    </p>
                    {action.reason && (
                      <p className="text-dark-400 text-sm mt-1">Reason: {action.reason}</p>
                    )}
                    <p className="text-dark-500 text-sm mt-2">
                      {new Date(action.created_at).toLocaleString()}
                      {action.reversed && <span className="text-green-400 ml-2">• Reversed</span>}
                    </p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Message Results */}
      {activeTab === 'messages' && messageResults.length > 0 && (
        <div className="space-y-3">
          <p className="text-dark-400 text-sm">{messageResults.length} messages found</p>
          {messageResults.map(msg => (
            <Card key={msg.id} className="hover:border-dark-700 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                  {msg.user.first_name.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white">{msg.user.first_name}</span>
                    <span className="text-dark-500 text-sm">
                      {new Date(msg.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-dark-300">{msg.content}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-0.5 bg-dark-800 rounded text-xs text-dark-400">
                      {msg.message_type}
                    </span>
                    {msg.has_media && (
                      <span className="px-2 py-0.5 bg-indigo-500/20 rounded text-xs text-indigo-400">
                        Has Media
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Recent Searches */}
      {activeTab === 'search' && results.length === 0 && !loading && recentSearches.length > 0 && (
        <Card title="Recent Searches" icon={History}>
          <div className="flex flex-wrap gap-2 mt-4">
            {recentSearches.map((search, i) => (
              <button
                key={i}
                onClick={() => {
                  setQuery(search)
                  handleSearch()
                }}
                className="px-3 py-1.5 bg-dark-800 hover:bg-dark-700 rounded-lg text-sm text-dark-300 transition-colors"
              >
                {search}
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Total Messages" value={stats.total_messages.toLocaleString()} icon={MessageSquare} />
            <StatCard title="Total Users" value={stats.total_users.toLocaleString()} icon={User} />
            <StatCard title="Moderations" value={stats.total_moderations.toLocaleString()} icon={Shield} />
            <StatCard title="Notes" value={stats.total_notes.toLocaleString()} icon={FileText} />
          </div>

          <Card title="Searchable Content" icon={BarChart3}>
            <div className="mt-4 space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-dark-300">Messages</span>
                  <span className="text-dark-400">{stats.total_messages.toLocaleString()}</span>
                </div>
                <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: '100%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-dark-300">Users</span>
                  <span className="text-dark-400">{stats.total_users.toLocaleString()}</span>
                </div>
                <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 rounded-full" 
                    style={{ width: `${(stats.total_users / stats.total_messages) * 100}%` }} 
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-dark-300">Moderations</span>
                  <span className="text-dark-400">{stats.total_moderations.toLocaleString()}</span>
                </div>
                <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-red-500 rounded-full" 
                    style={{ width: `${(stats.total_moderations / stats.total_messages) * 100}%` }} 
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* No Results */}
      {!loading && ((activeTab === 'search' && results.length === 0 && query) ||
        (activeTab === 'users' && userResults.length === 0 && query) ||
        (activeTab === 'moderation' && moderationResults.length === 0 && query) ||
        (activeTab === 'messages' && messageResults.length === 0 && query)) && (
        <Card>
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <p className="text-dark-400">No results found</p>
            <p className="text-sm text-dark-500 mt-1">Try adjusting your search terms or filters</p>
          </div>
        </Card>
      )}
    </div>
  )
}
