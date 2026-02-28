import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  FileText,
  Filter,
  Plus,
  Search,
  Edit2,
  Trash2,
  Copy,
  Play,
  Hash,
  MessageCircle,
  Image,
  File,
  Volume2,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react'
import { getNotes, createNote, updateNote, deleteNote, getFilters, createFilter, deleteFilter } from '../../api/notes'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'
import Modal from 'react-modal'

Modal.setAppElement('#root')

interface Note {
  id: number
  keyword: string
  content: string
  is_private: boolean
  has_buttons: boolean
  media_file_id: string | null
  media_type: string | null
  created_at: string
}

interface FilterItem {
  id: number
  trigger: string
  match_type: string
  response_type: string
  response_content: string
  action: string | null
  delete_trigger: boolean
  admin_only: boolean
  case_sensitive: boolean
}

export default function NotesAndFilters() {
  const { groupId } = useParams<{ groupId: string }>()
  const [notes, setNotes] = useState<Note[]>([])
  const [filters, setFilters] = useState<FilterItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'notes' | 'filters'>('notes')
  const [searchQuery, setSearchQuery] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Note | FilterItem | null>(null)
  const [formData, setFormData] = useState({
    keyword: '',
    content: '',
    is_private: false,
    match_type: 'contains',
    response_type: 'text',
    action: 'none',
    delete_trigger: false,
    admin_only: false,
    case_sensitive: false,
  })

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)
    try {
      const [notesData, filtersData] = await Promise.all([
        getNotes(parseInt(groupId)),
        getFilters(parseInt(groupId)),
      ])
      setNotes(notesData.items || notesData || [])
      setFilters(filtersData.items || filtersData || [])
    } catch (error) {
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [groupId])

  const handleSave = async () => {
    if (!groupId) return
    try {
      if (activeTab === 'notes') {
        if (editingItem) {
          await updateNote(parseInt(groupId), editingItem.id, {
            content: formData.content,
            is_private: formData.is_private,
          })
          toast.success('Note updated')
        } else {
          await createNote(parseInt(groupId), {
            keyword: formData.keyword,
            content: formData.content,
            is_private: formData.is_private,
          })
          toast.success('Note created')
        }
      } else {
        await createFilter(parseInt(groupId), {
          trigger: formData.keyword,
          match_type: formData.match_type,
          response_type: formData.response_type,
          response_content: formData.content,
          action: formData.action,
          delete_trigger: formData.delete_trigger,
          admin_only: formData.admin_only,
          case_sensitive: formData.case_sensitive,
        })
        toast.success('Filter created')
      }
      setModalOpen(false)
      setEditingItem(null)
      setFormData({
        keyword: '',
        content: '',
        is_private: false,
        match_type: 'contains',
        response_type: 'text',
        action: 'none',
        delete_trigger: false,
        admin_only: false,
        case_sensitive: false,
      })
      loadData()
    } catch (error) {
      toast.error('Failed to save')
    }
  }

  const handleDelete = async (id: number) => {
    if (!groupId) return
    if (!confirm('Are you sure you want to delete this item?')) return
    try {
      if (activeTab === 'notes') {
        await deleteNote(parseInt(groupId), id)
        setNotes(notes.filter((n) => n.id !== id))
      } else {
        await deleteFilter(parseInt(groupId), id)
        setFilters(filters.filter((f) => f.id !== id))
      }
      toast.success('Deleted successfully')
    } catch (error) {
      toast.error('Failed to delete')
    }
  }

  const filteredNotes = notes.filter(
    (n) =>
      n.keyword.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredFilters = filters.filter(
    (f) =>
      f.trigger.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.response_content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getMediaIcon = (type: string | null) => {
    switch (type) {
      case 'photo':
        return <Image className="w-4 h-4" />
      case 'video':
        return <File className="w-4 h-4" />
      case 'audio':
      case 'voice':
        return <Volume2 className="w-4 h-4" />
      default:
        return <MessageCircle className="w-4 h-4" />
    }
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Notes & Filters</h1>
          <p className="text-dark-400 mt-1">Manage saved notes and keyword responses</p>
        </div>
        <button
          onClick={() => {
            setEditingItem(null)
            setFormData({
              keyword: '',
              content: '',
              is_private: false,
              match_type: 'contains',
              response_type: 'text',
              action: 'none',
              delete_trigger: false,
              admin_only: false,
              case_sensitive: false,
            })
            setModalOpen(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add {activeTab === 'notes' ? 'Note' : 'Filter'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('notes')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'notes'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <Hash className="w-4 h-4 inline mr-2" />
          Notes ({notes.length})
        </button>
        <button
          onClick={() => setActiveTab('filters')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'filters'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <Filter className="w-4 h-4 inline mr-2" />
          Filters ({filters.length})
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-500" />
        <input
          type="text"
          placeholder={`Search ${activeTab}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-dark-900 border border-dark-800 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
        />
      </div>

      {/* Items Grid */}
      <div className="grid gap-4">
        {(activeTab === 'notes' ? filteredNotes : filteredFilters).map((item) => (
          <Card key={item.id} className="hover:border-dark-700 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-primary-400 font-mono text-lg">#{(item as Note).keyword || (item as FilterItem).trigger}</span>
                  {(item as Note).is_private && (
                    <span className="px-2 py-0.5 bg-dark-700 rounded text-xs text-dark-400">Private</span>
                  )}
                  {(item as FilterItem).admin_only && (
                    <span className="px-2 py-0.5 bg-purple-500/20 rounded text-xs text-purple-400">Admin Only</span>
                  )}
                  {(item as FilterItem).case_sensitive && (
                    <span className="px-2 py-0.5 bg-dark-700 rounded text-xs text-dark-400">Case Sensitive</span>
                  )}
                </div>
                <p className="text-dark-300 text-sm line-clamp-2">
                  {(item as Note).content || (item as FilterItem).response_content}
                </p>
                {activeTab === 'filters' && (
                  <div className="flex items-center gap-4 mt-2 text-xs text-dark-500">
                    <span>Match: {(item as FilterItem).match_type}</span>
                    <span>Response: {(item as FilterItem).response_type}</span>
                    {(item as FilterItem).action && <span>Action: {(item as FilterItem).action}</span>}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 ml-4">
                <button
                  onClick={() => {
                    const text = (item as Note).keyword || (item as FilterItem).trigger
                    navigator.clipboard.writeText(`#${text}`)
                    toast.success('Copied to clipboard')
                  }}
                  className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                >
                  <Copy className="w-4 h-4 text-dark-400" />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {(activeTab === 'notes' ? filteredNotes : filteredFilters).length === 0 && (
        <div className="text-center py-12">
          {activeTab === 'notes' ? (
            <FileText className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          ) : (
            <Filter className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          )}
          <h3 className="text-lg font-medium text-dark-300">
            No {activeTab} found
          </h3>
          <p className="text-dark-500">
            {searchQuery ? 'Try a different search term' : `Create your first ${activeTab.slice(0, -1)}`}
          </p>
        </div>
      )}

      {/* Modal */}
      <Modal
        isOpen={modalOpen}
        onRequestClose={() => setModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">
            {editingItem ? 'Edit' : 'Add'} {activeTab === 'notes' ? 'Note' : 'Filter'}
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                {activeTab === 'notes' ? 'Keyword (#keyword)' : 'Trigger'}
              </label>
              <input
                type="text"
                value={formData.keyword}
                onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
                placeholder={activeTab === 'notes' ? 'note_name' : 'trigger word'}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
                disabled={!!editingItem}
              />
            </div>

            {activeTab === 'filters' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Match Type</label>
                  <select
                    value={formData.match_type}
                    onChange={(e) => setFormData({ ...formData, match_type: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="exact">Exact Match</option>
                    <option value="contains">Contains</option>
                    <option value="startswith">Starts With</option>
                    <option value="endswith">Ends With</option>
                    <option value="regex">Regex</option>
                  </select>
                </div>

                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.case_sensitive}
                      onChange={(e) => setFormData({ ...formData, case_sensitive: e.target.checked })}
                      className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-dark-300">Case Sensitive</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.admin_only}
                      onChange={(e) => setFormData({ ...formData, admin_only: e.target.checked })}
                      className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-dark-300">Admin Only</span>
                  </label>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                {activeTab === 'notes' ? 'Content' : 'Response'}
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                placeholder={activeTab === 'notes' ? 'Note content...' : 'Response content...'}
                rows={4}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500 resize-none"
              />
            </div>

            {activeTab === 'notes' && (
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_private}
                  onChange={(e) => setFormData({ ...formData, is_private: e.target.checked })}
                  className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-dark-300">Private (send via DM)</span>
              </label>
            )}

            {activeTab === 'filters' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Response Type</label>
                  <select
                    value={formData.response_type}
                    onChange={(e) => setFormData({ ...formData, response_type: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="text">Text</option>
                    <option value="photo">Photo</option>
                    <option value="video">Video</option>
                    <option value="sticker">Sticker</option>
                    <option value="document">Document</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Action</label>
                  <select
                    value={formData.action}
                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="none">None</option>
                    <option value="delete">Delete Message</option>
                    <option value="warn">Warn</option>
                    <option value="mute">Mute</option>
                    <option value="ban">Ban</option>
                  </select>
                </div>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.delete_trigger}
                    onChange={(e) => setFormData({ ...formData, delete_trigger: e.target.checked })}
                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-dark-300">Delete trigger message</span>
                </label>
              </>
            )}
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setModalOpen(false)}
              className="flex-1 px-4 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!formData.keyword || !formData.content}
              className="flex-1 px-4 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Save
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
