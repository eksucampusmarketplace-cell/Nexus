import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Type,
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Code,
  Link,
  Image as ImageIcon,
  Smile,
  Hash,
  LayoutTemplate,
  Plus,
  Trash2,
  Copy,
  Check,
  Eye,
  Grid3X3,
  Type as TypeIcon,
  Palette,
  Sparkles,
  Save,
  X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../../components/UI/Card'
import Loading from '../../components/UI/Loading'
import Modal from 'react-modal'
import * as formattingAPI from '../../api/formatting'

Modal.setAppElement('#root')

type TabType = 'editor' | 'templates' | 'buttons' | 'variables'

interface FormattingState {
  bold: boolean
  italic: boolean
  underline: boolean
  strikethrough: boolean
  spoiler: boolean
  code: boolean
  pre: boolean
}

export default function FormattingTools() {
  const { groupId } = useParams<{ groupId: string }>()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('editor')
  const [templates, setTemplates] = useState<formattingAPI.TextTemplate[]>([])
  const [buttonConfigs, setButtonConfigs] = useState<formattingAPI.ButtonConfig[]>([])
  const [variables, setVariables] = useState<Record<string, string>>({})
  
  // Editor state
  const [content, setContent] = useState('')
  const [formatting, setFormatting] = useState<FormattingState>({
    bold: false,
    italic: false,
    underline: false,
    strikethrough: false,
    spoiler: false,
    code: false,
    pre: false
  })
  const [preview, setPreview] = useState('')
  const [copied, setCopied] = useState(false)
  
  // Modal states
  const [saveTemplateModalOpen, setSaveTemplateModalOpen] = useState(false)
  const [templateForm, setTemplateForm] = useState({ name: '', category: 'custom' as const })
  
  // Button builder state
  const [buttonRows, setButtonRows] = useState<formattingAPI.ButtonRow[]>([
    {
      id: 'row-1',
      buttons: [
        { id: 'btn-1', text: 'Button 1', type: 'url', value: 'https://', style: 'primary' }
      ]
    }
  ])

  useEffect(() => {
    loadData()
  }, [groupId, activeTab])

  useEffect(() => {
    // Generate preview when content changes
    let previewText = content
    if (formatting.bold) previewText = `<b>${previewText}</b>`
    if (formatting.italic) previewText = `<i>${previewText}</i>`
    if (formatting.underline) previewText = `<u>${previewText}</u>`
    if (formatting.strikethrough) previewText = `<s>${previewText}</s>`
    if (formatting.spoiler) previewText = `<tg-spoiler>${previewText}</tg-spoiler>`
    if (formatting.code) previewText = `<code>${previewText}</code>`
    if (formatting.pre) previewText = `<pre>${previewText}</pre>`
    setPreview(previewText)
  }, [content, formatting])

  const loadData = async () => {
    if (!groupId) return
    setLoading(true)

    try {
      switch (activeTab) {
        case 'templates':
          const templatesRes = await formattingAPI.getTextTemplates(parseInt(groupId))
          setTemplates(templatesRes)
          break
        case 'buttons':
          const buttonsRes = await formattingAPI.getButtonConfigs(parseInt(groupId))
          setButtonConfigs(buttonsRes)
          break
        case 'variables':
          const varsRes = await formattingAPI.getVariableReference(parseInt(groupId))
          setVariables(varsRes)
          break
      }
    } catch (error) {
      console.error('Failed to load formatting data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleFormatting = (key: keyof FormattingState) => {
    setFormatting(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(preview)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    toast.success('Copied to clipboard!')
  }

  const handleSaveTemplate = async () => {
    if (!groupId || !templateForm.name || !content) return
    try {
      await formattingAPI.createTextTemplate(parseInt(groupId), {
        name: templateForm.name,
        content,
        category: templateForm.category,
        variables: Object.keys(variables)
      })
      toast.success('Template saved!')
      setSaveTemplateModalOpen(false)
      setTemplateForm({ name: '', category: 'custom' })
      loadData()
    } catch (error) {
      toast.error('Failed to save template')
    }
  }

  const addButtonRow = () => {
    setButtonRows(prev => [...prev, {
      id: `row-${Date.now()}`,
      buttons: [
        { id: `btn-${Date.now()}`, text: 'New Button', type: 'url', value: '', style: 'primary' }
      ]
    }])
  }

  const addButtonToRow = (rowIndex: number) => {
    setButtonRows(prev => prev.map((row, i) => 
      i === rowIndex
        ? {
            ...row,
            buttons: [...row.buttons, {
              id: `btn-${Date.now()}`,
              text: 'New Button',
              type: 'url',
              value: '',
              style: 'primary'
            }]
          }
        : row
    ))
  }

  const updateButton = (rowIndex: number, buttonIndex: number, updates: Partial<any>) => {
    setButtonRows(prev => prev.map((row, i) =>
      i === rowIndex
        ? {
            ...row,
            buttons: row.buttons.map((btn, j) =>
              j === buttonIndex ? { ...btn, ...updates } : btn
            )
          }
        : row
    ))
  }

  const removeButton = (rowIndex: number, buttonIndex: number) => {
    setButtonRows(prev => prev.map((row, i) =>
      i === rowIndex
        ? { ...row, buttons: row.buttons.filter((_, j) => j !== buttonIndex) }
        : row
    ).filter(row => row.buttons.length > 0))
  }

  const generateButtonCode = async () => {
    if (!groupId) return
    try {
      const result = await formattingAPI.generateButtonCode(parseInt(groupId), buttonRows)
      navigator.clipboard.writeText(result.code)
      toast.success('Button code copied!')
    } catch (error) {
      toast.error('Failed to generate button code')
    }
  }

  const formatText = (text: string, type: string) => {
    switch (type) {
      case 'bold': return `<b>${text}</b>`
      case 'italic': return `<i>${text}</i>`
      case 'underline': return `<u>${text}</u>`
      case 'strikethrough': return `<s>${text}</s>`
      case 'spoiler': return `<tg-spoiler>${text}</tg-spoiler>`
      case 'code': return `<code>${text}</code>`
      case 'pre': return `<pre>${text}</pre>`
      case 'link': return `<a href="https://">${text}</a>`
      default: return text
    }
  }

  const insertFormat = (type: string) => {
    const textarea = document.getElementById('editor') as HTMLTextAreaElement
    if (!textarea) return
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selectedText = content.substring(start, end)
    const formatted = formatText(selectedText || 'text', type)
    
    const newContent = content.substring(0, start) + formatted + content.substring(end)
    setContent(newContent)
  }

  if (loading) {
    return <Loading />
  }

  return (
    <div className="py-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-xl flex items-center justify-center">
            <Type className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Formatting & Content</h1>
            <p className="text-dark-400 mt-1">Rich text tools, button generator, templates</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {[
          { id: 'editor', label: 'Text Editor', icon: TypeIcon },
          { id: 'templates', label: 'Templates', icon: LayoutTemplate },
          { id: 'buttons', label: 'Button Builder', icon: Grid3X3 },
          { id: 'variables', label: 'Variables', icon: Hash },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Editor Tab */}
      {activeTab === 'editor' && (
        <div className="space-y-6">
          {/* Toolbar */}
          <Card>
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'bold', icon: Bold, label: 'Bold' },
                { key: 'italic', icon: Italic, label: 'Italic' },
                { key: 'underline', icon: Underline, label: 'Underline' },
                { key: 'strikethrough', icon: Strikethrough, label: 'Strike' },
                { key: 'spoiler', icon: Eye, label: 'Spoiler' },
                { key: 'code', icon: Code, label: 'Code' },
                { key: 'pre', icon: Code, label: 'Pre' },
                { key: 'link', icon: Link, label: 'Link' },
              ].map(({ key, icon: Icon, label }) => (
                <button
                  key={key}
                  onClick={() => insertFormat(key)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg transition-colors ${
                    (formatting as any)[key]
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm">{label}</span>
                </button>
              ))}
            </div>
          </Card>

          {/* Editor */}
          <Card>
            <div className="mb-4">
              <label className="block text-sm font-medium text-dark-300 mb-2">Content</label>
              <textarea
                id="editor"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Type your message here..."
                rows={6}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-emerald-500 resize-none"
              />
            </div>

            {/* Preview */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-dark-300">Preview</label>
                <button
                  onClick={copyToClipboard}
                  className="flex items-center gap-1 text-sm text-emerald-400 hover:text-emerald-300"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <div className="p-4 bg-dark-800 rounded-xl">
                <code className="text-sm text-dark-300 break-all">{preview}</code>
              </div>
            </div>

            <button
              onClick={() => setSaveTemplateModalOpen(true)}
              disabled={!content}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl text-white font-medium transition-colors"
            >
              <Save className="w-4 h-4 inline mr-2" />
              Save as Template
            </button>
          </Card>

          {/* Quick Variables */}
          <Card title="Quick Variables" icon={Hash}>
            <div className="flex flex-wrap gap-2 mt-4">
              {['{user}', '{group}', '{mention}', '{time}', '{date}', '{count}'].map(variable => (
                <button
                  key={variable}
                  onClick={() => setContent(prev => prev + variable)}
                  className="px-3 py-1.5 bg-dark-800 hover:bg-dark-700 rounded-lg text-sm text-emerald-400 transition-colors"
                >
                  {variable}
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.length === 0 ? (
              <Card className="md:col-span-2">
                <div className="text-center py-12">
                  <LayoutTemplate className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                  <p className="text-dark-400">No templates saved</p>
                  <p className="text-sm text-dark-500 mt-1">Create templates from the text editor</p>
                </div>
              </Card>
            ) : (
              templates.map(template => (
                <Card key={template.id} className="hover:border-dark-700 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-white">{template.name}</h4>
                      <span className="px-2 py-0.5 bg-dark-800 rounded text-xs text-dark-400">
                        {template.category}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        setContent(template.content)
                        setActiveTab('editor')
                        toast.success('Template loaded')
                      }}
                      className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    >
                      <Copy className="w-4 h-4 text-emerald-400" />
                    </button>
                  </div>
                  <p className="text-dark-400 text-sm line-clamp-3">{template.content}</p>
                  {template.variables.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                      {template.variables.map(v => (
                        <span key={v} className="px-2 py-0.5 bg-emerald-500/10 rounded text-xs text-emerald-400">
                          {'{'}{v}{'}'}
                        </span>
                      ))}
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Button Builder Tab */}
      {activeTab === 'buttons' && (
        <div className="space-y-6">
          <Card>
            <div className="space-y-4">
              {buttonRows.map((row, rowIndex) => (
                <div key={row.id} className="p-4 bg-dark-800/50 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-dark-400">Row {rowIndex + 1}</span>
                    <button
                      onClick={() => setButtonRows(prev => prev.filter((_, i) => i !== rowIndex))}
                      className="p-1 hover:bg-dark-700 rounded"
                    >
                      <X className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                  <div className="space-y-2">
                    {row.buttons.map((button, buttonIndex) => (
                      <div key={button.id} className="flex gap-2">
                        <input
                          type="text"
                          value={button.text}
                          onChange={(e) => updateButton(rowIndex, buttonIndex, { text: e.target.value })}
                          placeholder="Button text"
                          className="flex-1 px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white text-sm"
                        />
                        <select
                          value={button.type}
                          onChange={(e) => updateButton(rowIndex, buttonIndex, { type: e.target.value })}
                          className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white text-sm"
                        >
                          <option value="url">URL</option>
                          <option value="callback">Callback</option>
                          <option value="switch_inline">Inline</option>
                        </select>
                        <input
                          type="text"
                          value={button.value}
                          onChange={(e) => updateButton(rowIndex, buttonIndex, { value: e.target.value })}
                          placeholder="URL or data"
                          className="flex-1 px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white text-sm"
                        />
                        <select
                          value={button.style}
                          onChange={(e) => updateButton(rowIndex, buttonIndex, { style: e.target.value })}
                          className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-white text-sm"
                        >
                          <option value="primary">Primary</option>
                          <option value="secondary">Secondary</option>
                          <option value="danger">Danger</option>
                        </select>
                        <button
                          onClick={() => removeButton(rowIndex, buttonIndex)}
                          className="p-2 hover:bg-dark-700 rounded-lg"
                        >
                          <X className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => addButtonToRow(rowIndex)}
                    disabled={row.buttons.length >= 3}
                    className="mt-2 text-sm text-emerald-400 hover:text-emerald-300 disabled:opacity-50"
                  >
                    + Add Button to Row
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={addButtonRow}
              disabled={buttonRows.length >= 3}
              className="w-full mt-4 py-3 border-2 border-dashed border-dark-700 hover:border-emerald-500/50 rounded-xl text-dark-400 hover:text-emerald-400 transition-colors"
            >
              <Plus className="w-5 h-5 inline mr-2" />
              Add Row
            </button>

            <button
              onClick={generateButtonCode}
              disabled={buttonRows.length === 0}
              className="w-full mt-4 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl text-white font-medium transition-colors"
            >
              <Copy className="w-4 h-4 inline mr-2" />
              Copy Button Code
            </button>
          </Card>
        </div>
      )}

      {/* Variables Tab */}
      {activeTab === 'variables' && (
        <div className="space-y-6">
          <Card title="Available Variables" icon={Hash}>
            <div className="grid gap-3 mt-4">
              {Object.entries(variables).map(([key, description]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-dark-800/50 rounded-xl">
                  <code className="text-emerald-400">{'{'}{key}{'}'}</code>
                  <span className="text-dark-400 text-sm">{description}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`{${key}}`)
                      toast.success('Copied!')
                    }}
                    className="p-2 hover:bg-dark-700 rounded-lg"
                  >
                    <Copy className="w-4 h-4 text-dark-400" />
                  </button>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Usage Examples" icon={Sparkles}>
            <div className="space-y-3 mt-4">
              <div className="p-3 bg-dark-800/50 rounded-xl">
                <p className="text-dark-300 text-sm">Welcome message:</p>
                <code className="text-emerald-400 text-sm block mt-1">
                  Welcome {'{user}'} to {'{group}'}!
                </code>
              </div>
              <div className="p-3 bg-dark-800/50 rounded-xl">
                <p className="text-dark-300 text-sm">Stats display:</p>
                <code className="text-emerald-400 text-sm block mt-1">
                  You have {'{xp}'} XP and are level {'{level}'}
                </code>
              </div>
              <div className="p-3 bg-dark-800/50 rounded-xl">
                <p className="text-dark-300 text-sm">Mention users:</p>
                <code className="text-emerald-400 text-sm block mt-1">
                  Hey {'{mention}'}, check this out!
                </code>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Save Template Modal */}
      <Modal
        isOpen={saveTemplateModalOpen}
        onRequestClose={() => setSaveTemplateModalOpen(false)}
        className="fixed inset-0 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm z-50"
        overlayClassName="fixed inset-0 bg-black/50"
      >
        <div className="bg-dark-900 rounded-2xl p-6 w-full max-w-md border border-dark-800">
          <h2 className="text-xl font-bold text-white mb-6">Save Template</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Template Name</label>
              <input
                type="text"
                value={templateForm.name}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Welcome Message"
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-dark-500 focus:outline-none focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Category</label>
              <select
                value={templateForm.category}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, category: e.target.value as any }))}
                className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-primary-500"
              >
                <option value="welcome">Welcome</option>
                <option value="rules">Rules</option>
                <option value="announcement">Announcement</option>
                <option value="moderation">Moderation</option>
                <option value="fun">Fun</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setSaveTemplateModalOpen(false)}
              className="flex-1 py-3 bg-dark-800 hover:bg-dark-700 rounded-xl text-dark-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveTemplate}
              disabled={!templateForm.name}
              className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 rounded-xl text-white transition-colors disabled:opacity-50"
            >
              Save Template
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
