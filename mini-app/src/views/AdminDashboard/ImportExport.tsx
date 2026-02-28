import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import {
  Download,
  Upload,
  FileJson,
  FileArchive,
  Settings,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Database,
  Users,
  Shield,
  MessageSquare,
  FileText,
  Filter,
  Lock,
  Ban,
} from 'lucide-react'
import { exportGroup, getExportStatus, importGroup, getImportStatus } from '../../api/portability'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import toast from 'react-hot-toast'

const moduleOptions = [
  { id: 'admin', label: 'Admin Settings', icon: Shield },
  { id: 'antiflood', label: 'Anti-Flood', icon: Shield },
  { id: 'blocklist', label: 'Blocklist', icon: Ban },
  { id: 'disabled', label: 'Disabled Commands', icon: Settings },
  { id: 'filters', label: 'Filters', icon: Filter },
  { id: 'greetings', label: 'Greetings', icon: MessageSquare },
  { id: 'locks', label: 'Locks', icon: Lock },
  { id: 'notes', label: 'Notes', icon: FileText },
  { id: 'rules', label: 'Rules', icon: FileText },
]

export default function ImportExport() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'export' | 'import'>('export')
  const [selectedModules, setSelectedModules] = useState<string[]>([])
  const [exportFormat, setExportFormat] = useState<'json' | 'zip'>('json')
  const [exportStatus, setExportStatus] = useState<{ job_id: number; status: string; file_url?: string } | null>(null)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importMerge, setImportMerge] = useState(false)
  const [importStatus, setImportStatus] = useState<{ job_id: number; status: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleExport = async () => {
    if (!groupId) return
    if (selectedModules.length === 0) {
      toast.error('Please select at least one module')
      return
    }
    setLoading(true)
    try {
      const result = await exportGroup(parseInt(groupId), selectedModules, exportFormat)
      setExportStatus(result)
      toast.success('Export started')
      
      // Poll for status
      const pollStatus = async () => {
        const status = await getExportStatus(parseInt(groupId), result.id)
        setExportStatus(status)
        if (status.status === 'completed') {
          toast.success('Export completed!')
        } else if (status.status === 'failed') {
          toast.error('Export failed')
        } else {
          setTimeout(pollStatus, 2000)
        }
      }
      setTimeout(pollStatus, 2000)
    } catch (error) {
      toast.error('Failed to start export')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (!groupId || !importFile) return
    setLoading(true)
    try {
      const result = await importGroup(parseInt(groupId), importFile, selectedModules, importMerge)
      setImportStatus(result)
      toast.success('Import started')
      
      // Poll for status
      const pollStatus = async () => {
        const status = await getImportStatus(parseInt(groupId), result.id)
        setImportStatus(status)
        if (status.status === 'completed') {
          toast.success(`Import completed! ${status.imported_count || 0} items imported`)
        } else if (status.status === 'failed') {
          toast.error('Import failed')
        } else {
          setTimeout(pollStatus, 2000)
        }
      }
      setTimeout(pollStatus, 2000)
    } catch (error) {
      toast.error('Failed to start import')
    } finally {
      setLoading(false)
    }
  }

  const toggleModule = (moduleId: string) => {
    setSelectedModules((prev) =>
      prev.includes(moduleId) ? prev.filter((m) => m !== moduleId) : [...prev, moduleId]
    )
  }

  const selectAll = () => {
    setSelectedModules(moduleOptions.map((m) => m.id))
  }

  const selectNone = () => {
    setSelectedModules([])
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-400" />
      default:
        return <Clock className="w-5 h-5 text-yellow-400 animate-pulse" />
    }
  }

  return (
    <div className="py-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Import / Export</h1>
        <p className="text-dark-400 mt-1">Transfer settings between groups</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('export')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'export'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <Download className="w-4 h-4" />
          Export
        </button>
        <button
          onClick={() => setActiveTab('import')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'import'
              ? 'bg-primary-600 text-white'
              : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
          }`}
        >
          <Upload className="w-4 h-4" />
          Import
        </button>
      </div>

      {/* Export Tab */}
      {activeTab === 'export' && (
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Select Modules to Export</h3>
            <div className="flex gap-2 mb-4">
              <button
                onClick={selectAll}
                className="px-3 py-1 bg-dark-800 rounded-lg text-sm text-dark-400 hover:text-white"
              >
                Select All
              </button>
              <button
                onClick={selectNone}
                className="px-3 py-1 bg-dark-800 rounded-lg text-sm text-dark-400 hover:text-white"
              >
                Select None
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {moduleOptions.map((module) => (
                <label
                  key={module.id}
                  className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                    selectedModules.includes(module.id)
                      ? 'bg-primary-600/20 border border-primary-500'
                      : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModules.includes(module.id)}
                    onChange={() => toggleModule(module.id)}
                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
                  />
                  <module.icon className="w-5 h-5 text-dark-400" />
                  <span className="text-white text-sm">{module.label}</span>
                </label>
              ))}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Export Format</h3>
            <div className="flex gap-4">
              <label
                className={`flex-1 p-4 rounded-xl cursor-pointer transition-colors ${
                  exportFormat === 'json'
                    ? 'bg-primary-600/20 border border-primary-500'
                    : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                }`}
              >
                <input
                  type="radio"
                  name="format"
                  value="json"
                  checked={exportFormat === 'json'}
                  onChange={() => setExportFormat('json')}
                  className="sr-only"
                />
                <FileJson className="w-8 h-8 text-blue-400 mb-2" />
                <div className="font-medium text-white">JSON</div>
                <p className="text-dark-400 text-sm">Human-readable, easy to edit</p>
              </label>
              <label
                className={`flex-1 p-4 rounded-xl cursor-pointer transition-colors ${
                  exportFormat === 'zip'
                    ? 'bg-primary-600/20 border border-primary-500'
                    : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                }`}
              >
                <input
                  type="radio"
                  name="format"
                  value="zip"
                  checked={exportFormat === 'zip'}
                  onChange={() => setExportFormat('zip')}
                  className="sr-only"
                />
                <FileArchive className="w-8 h-8 text-purple-400 mb-2" />
                <div className="font-medium text-white">ZIP</div>
                <p className="text-dark-400 text-sm">Compressed, includes media</p>
              </label>
            </div>
          </Card>

          {exportStatus && (
            <Card>
              <div className="flex items-center gap-3">
                {getStatusIcon(exportStatus.status)}
                <div>
                  <div className="font-medium text-white capitalize">Export {exportStatus.status}</div>
                  {exportStatus.status === 'completed' && exportStatus.file_url && (
                    <a
                      href={exportStatus.file_url}
                      download
                      className="text-primary-400 text-sm hover:underline"
                    >
                      Download file
                    </a>
                  )}
                </div>
              </div>
            </Card>
          )}

          <button
            onClick={handleExport}
            disabled={loading || selectedModules.length === 0}
            className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Download className="w-5 h-5" />
            )}
            {loading ? 'Exporting...' : 'Start Export'}
          </button>
        </div>
      )}

      {/* Import Tab */}
      {activeTab === 'import' && (
        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Upload Export File</h3>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-dark-700 rounded-xl p-8 text-center cursor-pointer hover:border-primary-500 transition-colors"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,.zip"
                onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              {importFile ? (
                <div className="flex items-center justify-center gap-2">
                  <FileArchive className="w-8 h-8 text-primary-400" />
                  <span className="text-white">{importFile.name}</span>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-dark-500 mx-auto mb-4" />
                  <p className="text-dark-400">Click to upload export file</p>
                  <p className="text-dark-500 text-sm mt-2">Supports .json and .zip files</p>
                </>
              )}
            </div>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-white mb-4">Select Modules to Import</h3>
            <div className="flex gap-2 mb-4">
              <button
                onClick={selectAll}
                className="px-3 py-1 bg-dark-800 rounded-lg text-sm text-dark-400 hover:text-white"
              >
                Select All
              </button>
              <button
                onClick={selectNone}
                className="px-3 py-1 bg-dark-800 rounded-lg text-sm text-dark-400 hover:text-white"
              >
                Select None
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {moduleOptions.map((module) => (
                <label
                  key={module.id}
                  className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                    selectedModules.includes(module.id)
                      ? 'bg-primary-600/20 border border-primary-500'
                      : 'bg-dark-800 border border-dark-700 hover:border-dark-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModules.includes(module.id)}
                    onChange={() => toggleModule(module.id)}
                    className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
                  />
                  <module.icon className="w-5 h-5 text-dark-400" />
                  <span className="text-white text-sm">{module.label}</span>
                </label>
              ))}
            </div>
          </Card>

          <Card>
            <label className="flex items-center gap-3 p-3 bg-dark-800 rounded-xl cursor-pointer">
              <input
                type="checkbox"
                checked={importMerge}
                onChange={(e) => setImportMerge(e.target.checked)}
                className="w-4 h-4 rounded border-dark-600 bg-dark-800 text-primary-600"
              />
              <div>
                <span className="text-white">Merge with existing</span>
                <p className="text-dark-400 text-sm">Keep existing settings and merge new ones</p>
              </div>
            </label>
          </Card>

          {importStatus && (
            <Card>
              <div className="flex items-center gap-3">
                {getStatusIcon(importStatus.status)}
                <div className="font-medium text-white capitalize">Import {importStatus.status}</div>
              </div>
            </Card>
          )}

          <button
            onClick={handleImport}
            disabled={loading || !importFile || selectedModules.length === 0}
            className="w-full py-3 bg-primary-600 hover:bg-primary-700 rounded-xl text-white disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Upload className="w-5 h-5" />
            )}
            {loading ? 'Importing...' : 'Start Import'}
          </button>
        </div>
      )}
    </div>
  )
}
