/**
 * Comprehensive API for managing all Nexus features via toggles
 * No need to send commands to groups - manage everything from the Mini App
 */

import api from './client'

// ============ Types ============

export interface ToggleState {
  module: string
  feature: string
  enabled: boolean
  config?: Record<string, any>
}

export interface ModuleToggle {
  name: string
  displayName: string
  description: string
  category: string
  icon: string
  enabled: boolean
  config: Record<string, any>
  features: FeatureToggle[]
}

export interface FeatureToggle {
  key: string
  label: string
  description: string
  type: 'boolean' | 'select' | 'number' | 'text' | 'duration' | 'time' | 'multiselect'
  value: any
  options?: { value: string; label: string }[]
  min?: number
  max?: number
  placeholder?: string
  dependsOn?: string
}

export interface QuickAction {
  id: string
  label: string
  icon: string
  description: string
  module: string
  action: string
  params?: Record<string, any>
  confirmRequired?: boolean
  confirmMessage?: string
}

// ============ Module Toggle API ============

export const toggleApi = {
  /**
   * Get all modules with their toggle states for a group
   */
  async getModules(groupId: number): Promise<ModuleToggle[]> {
    const response = await api.get(`/groups/${groupId}/toggles`)
    return response.data
  },

  /**
   * Toggle a module on/off
   */
  async toggleModule(groupId: number, moduleName: string, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/modules/${moduleName}`, { is_enabled: enabled })
  },

  /**
   * Update a feature configuration
   */
  async updateFeature(
    groupId: number,
    moduleName: string,
    featureKey: string,
    value: any
  ): Promise<void> {
    await api.patch(`/groups/${groupId}/modules/${moduleName}/features/${featureKey}`, { value })
  },

  /**
   * Batch update multiple features
   */
  async batchUpdate(
    groupId: number,
    updates: Array<{ module: string; feature: string; value: any }>
  ): Promise<void> {
    await api.post(`/groups/${groupId}/toggles/batch`, { updates })
  },

  /**
   * Reset module to defaults
   */
  async resetModule(groupId: number, moduleName: string): Promise<void> {
    await api.post(`/groups/${groupId}/modules/${moduleName}/reset`)
  },
}

// ============ Quick Actions API ============

export const quickActionsApi = {
  /**
   * Execute a quick action (like a command but via API)
   */
  async execute(groupId: number, action: QuickAction): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/groups/${groupId}/actions/execute`, action)
    return response.data
  },

  /**
   * Get available quick actions for a group
   */
  async getAvailable(groupId: number): Promise<QuickAction[]> {
    const response = await api.get(`/groups/${groupId}/actions`)
    return response.data
  },
}

// ============ Lock Toggles API ============

export const locksToggleApi = {
  /**
   * Get all lock states for a group
   */
  async getAll(groupId: number): Promise<Record<string, { locked: boolean; mode: string }>> {
    const response = await api.get(`/groups/${groupId}/locks`)
    return response.data
  },

  /**
   * Toggle a specific lock
   */
  async toggle(groupId: number, lockType: string, locked: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/locks/${lockType}`, { is_locked: locked })
  },

  /**
   * Set lock mode (delete, warn, mute, kick, ban)
   */
  async setMode(groupId: number, lockType: string, mode: string, duration?: number): Promise<void> {
    await api.patch(`/groups/${groupId}/locks/${lockType}/mode`, { mode, duration })
  },

  /**
   * Set timed lock
   */
  async setTimed(groupId: number, lockType: string, startTime: string, endTime: string): Promise<void> {
    await api.post(`/groups/${groupId}/locks/${lockType}/timed`, { start_time: startTime, end_time: endTime })
  },

  /**
   * Remove timed lock
   */
  async removeTimed(groupId: number, lockType: string): Promise<void> {
    await api.delete(`/groups/${groupId}/locks/${lockType}/timed`)
  },
}

// ============ Antispam Toggles API ============

export const antispamToggleApi = {
  /**
   * Get antispam configuration
   */
  async getConfig(groupId: number): Promise<{
    antiflood: { enabled: boolean; limit: number; window: number; action: string }
    antiraid: { enabled: boolean; threshold: number; window: number; action: string }
    cas: { enabled: boolean; action: string }
  }> {
    const response = await api.get(`/groups/${groupId}/antispam/config`)
    return response.data
  },

  /**
   * Toggle antiflood
   */
  async toggleAntiflood(groupId: number, enabled: boolean, config?: {
    limit?: number
    window?: number
    action?: string
  }): Promise<void> {
    await api.patch(`/groups/${groupId}/antispam/antiflood`, { enabled, ...config })
  },

  /**
   * Toggle antiraid
   */
  async toggleAntiraid(groupId: number, enabled: boolean, config?: {
    threshold?: number
    window?: number
    action?: string
  }): Promise<void> {
    await api.patch(`/groups/${groupId}/antispam/antiraid`, { enabled, ...config })
  },

  /**
   * Toggle CAS (Combot Anti-Spam)
   */
  async toggleCAS(groupId: number, enabled: boolean, action: string): Promise<void> {
    await api.patch(`/groups/${groupId}/antispam/cas`, { enabled, action })
  },
}

// ============ Welcome Toggles API ============

export const welcomeToggleApi = {
  /**
   * Get welcome configuration
   */
  async getConfig(groupId: number): Promise<{
    enabled: boolean
    message: string
    mediaType?: string
    mediaFileId?: string
    deleteAfter?: number
    sendAsDm: boolean
    showDate: boolean
    buttons: Array<{ text: string; url: string }>
    goodbyeEnabled: boolean
    goodbyeMessage?: string
  }> {
    const response = await api.get(`/groups/${groupId}/welcome/config`)
    return response.data
  },

  /**
   * Toggle welcome
   */
  async toggle(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/welcome`, { enabled })
  },

  /**
   * Set welcome message
   */
  async setMessage(groupId: number, message: string, mediaType?: string, mediaFileId?: string): Promise<void> {
    await api.put(`/groups/${groupId}/welcome/message`, { message, media_type: mediaType, media_file_id: mediaFileId })
  },

  /**
   * Add welcome button
   */
  async addButton(groupId: number, text: string, url: string): Promise<void> {
    await api.post(`/groups/${groupId}/welcome/buttons`, { text, url })
  },

  /**
   * Remove welcome button
   */
  async removeButton(groupId: number, index: number): Promise<void> {
    await api.delete(`/groups/${groupId}/welcome/buttons/${index}`)
  },

  /**
   * Toggle goodbye
   */
  async toggleGoodbye(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/welcome/goodbye`, { enabled })
  },

  /**
   * Set goodbye message
   */
  async setGoodbyeMessage(groupId: number, message: string): Promise<void> {
    await api.put(`/groups/${groupId}/welcome/goodbye/message`, { message })
  },
}

// ============ Captcha Toggles API ============

export const captchaToggleApi = {
  /**
   * Get captcha configuration
   */
  async getConfig(groupId: number): Promise<{
    enabled: boolean
    type: 'button' | 'math' | 'quiz' | 'image' | 'text'
    timeout: number
    actionOnFail: 'kick' | 'ban' | 'restrict'
    muteOnJoin: boolean
    customText?: string
  }> {
    const response = await api.get(`/groups/${groupId}/captcha/config`)
    return response.data
  },

  /**
   * Toggle captcha
   */
  async toggle(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/captcha`, { enabled })
  },

  /**
   * Set captcha type
   */
  async setType(groupId: number, type: string): Promise<void> {
    await api.patch(`/groups/${groupId}/captcha/type`, { type })
  },

  /**
   * Set captcha settings
   */
  async setSettings(groupId: number, settings: {
    timeout?: number
    actionOnFail?: string
    muteOnJoin?: boolean
    customText?: string
  }): Promise<void> {
    await api.patch(`/groups/${groupId}/captcha/settings`, settings)
  },
}

// ============ Moderation Toggles API ============

export const moderationToggleApi = {
  /**
   * Get moderation configuration
   */
  async getConfig(groupId: number): Promise<{
    warnThreshold: number
    warnAction: 'mute' | 'kick' | 'ban'
    warnDuration?: number
    silentMode: boolean
    logChannel?: number
    requireReason: boolean
  }> {
    const response = await api.get(`/groups/${groupId}/moderation/config`)
    return response.data
  },

  /**
   * Set warn threshold
   */
  async setWarnThreshold(groupId: number, threshold: number): Promise<void> {
    await api.patch(`/groups/${groupId}/moderation/warn-threshold`, { threshold })
  },

  /**
   * Set warn action
   */
  async setWarnAction(groupId: number, action: string, duration?: number): Promise<void> {
    await api.patch(`/groups/${groupId}/moderation/warn-action`, { action, duration })
  },

  /**
   * Toggle silent mode
   */
  async toggleSilentMode(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/moderation/silent-mode`, { enabled })
  },

  /**
   * Set log channel
   */
  async setLogChannel(groupId: number, channelId: number | null): Promise<void> {
    await api.patch(`/groups/${groupId}/moderation/log-channel`, { channel_id: channelId })
  },

  /**
   * Quick warn a user
   */
  async warnUser(groupId: number, userId: number, reason?: string): Promise<{ success: boolean; warnCount: number }> {
    const response = await api.post(`/groups/${groupId}/moderation/warn`, { user_id: userId, reason })
    return response.data
  },

  /**
   * Quick mute a user
   */
  async muteUser(groupId: number, userId: number, duration: string, reason?: string): Promise<{ success: boolean }> {
    const response = await api.post(`/groups/${groupId}/moderation/mute`, { user_id: userId, duration, reason })
    return response.data
  },

  /**
   * Quick ban a user
   */
  async banUser(groupId: number, userId: number, duration?: string, reason?: string): Promise<{ success: boolean }> {
    const response = await api.post(`/groups/${groupId}/moderation/ban`, { user_id: userId, duration, reason })
    return response.data
  },

  /**
   * Quick kick a user
   */
  async kickUser(groupId: number, userId: number, reason?: string): Promise<{ success: boolean }> {
    const response = await api.post(`/groups/${groupId}/moderation/kick`, { user_id: userId, reason })
    return response.data
  },
}

// ============ Rules Toggles API ============

export const rulesToggleApi = {
  /**
   * Get rules
   */
  async getRules(groupId: number): Promise<{
    enabled: boolean
    content: string
    showOnJoin: boolean
    sendAsDm: boolean
  }> {
    const response = await api.get(`/groups/${groupId}/rules`)
    return response.data
  },

  /**
   * Set rules
   */
  async setRules(groupId: number, content: string): Promise<void> {
    await api.put(`/groups/${groupId}/rules`, { content })
  },

  /**
   * Toggle show on join
   */
  async toggleShowOnJoin(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/rules/show-on-join`, { enabled })
  },
}

// ============ Silent Mode API ============

export const silentModeApi = {
  /**
   * Get silent mode status
   */
  async getStatus(groupId: number): Promise<{
    enabled: boolean
    scheduledWindows: Array<{ start: string; end: string }>
    until?: string
  }> {
    const response = await api.get(`/groups/${groupId}/silent-mode`)
    return response.data
  },

  /**
   * Enable silent mode immediately
   */
  async enable(groupId: number, duration?: string): Promise<void> {
    await api.post(`/groups/${groupId}/silent-mode/enable`, { duration })
  },

  /**
   * Disable silent mode
   */
  async disable(groupId: number): Promise<void> {
    await api.post(`/groups/${groupId}/silent-mode/disable`)
  },

  /**
   * Add scheduled window
   */
  async addWindow(groupId: number, startTime: string, endTime: string): Promise<void> {
    await api.post(`/groups/${groupId}/silent-mode/windows`, { start_time: startTime, end_time: endTime })
  },

  /**
   * Remove scheduled window
   */
  async removeWindow(groupId: number, index: number): Promise<void> {
    await api.delete(`/groups/${groupId}/silent-mode/windows/${index}`)
  },
}

// ============ Member Booster API ============

export const memberBoosterApi = {
  /**
   * Get member booster configuration
   */
  async getConfig(groupId: number): Promise<{
    forceAdd: { enabled: boolean; required: number; message?: string }
    forceChannel: { enabled: boolean; channels: Array<{ id: number; username?: string }> }
    forceBoost: { enabled: boolean }
  }> {
    const response = await api.get(`/groups/${groupId}/member-booster/config`)
    return response.data
  },

  /**
   * Toggle force add
   */
  async toggleForceAdd(groupId: number, enabled: boolean, required: number): Promise<void> {
    await api.patch(`/groups/${groupId}/member-booster/force-add`, { enabled, required })
  },

  /**
   * Toggle force channel
   */
  async toggleForceChannel(groupId: number, enabled: boolean, channelId: number): Promise<void> {
    await api.patch(`/groups/${groupId}/member-booster/force-channel`, { enabled, channel_id: channelId })
  },

  /**
   * Toggle force boost
   */
  async toggleForceBoost(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/member-booster/force-boost`, { enabled })
  },

  /**
   * Get top inviters
   */
  async getTopInviters(groupId: number, period: 'all' | '24h' = 'all'): Promise<Array<{
    userId: number
    name: string
    invites: number
  }>> {
    const response = await api.get(`/groups/${groupId}/member-booster/top`, { params: { period } })
    return response.data
  },
}

// ============ Word Filter API ============

export const wordFilterApi = {
  /**
   * Get word filter configuration
   */
  async getConfig(groupId: number): Promise<{
    filterList: { enabled: boolean; words: string[]; action: string }
    badList: { enabled: boolean; words: string[]; action: string; warnOnMatch: boolean }
  }> {
    const response = await api.get(`/groups/${groupId}/word-filter/config`)
    return response.data
  },

  /**
   * Add word to filter list
   */
  async addFilterWord(groupId: number, word: string): Promise<void> {
    await api.post(`/groups/${groupId}/word-filter/filter-list/words`, { word })
  },

  /**
   * Remove word from filter list
   */
  async removeFilterWord(groupId: number, word: string): Promise<void> {
    await api.delete(`/groups/${groupId}/word-filter/filter-list/words/${encodeURIComponent(word)}`)
  },

  /**
   * Add word to bad list
   */
  async addBadWord(groupId: number, word: string): Promise<void> {
    await api.post(`/groups/${groupId}/word-filter/bad-list/words`, { word })
  },

  /**
   * Remove word from bad list
   */
  async removeBadWord(groupId: number, word: string): Promise<void> {
    await api.delete(`/groups/${groupId}/word-filter/bad-list/words/${encodeURIComponent(word)}`)
  },

  /**
   * Set action for filter list
   */
  async setFilterAction(groupId: number, action: string): Promise<void> {
    await api.patch(`/groups/${groupId}/word-filter/filter-list/action`, { action })
  },

  /**
   * Set action for bad list
   */
  async setBadListAction(groupId: number, action: string, warnOnMatch: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/word-filter/bad-list/action`, { action, warn_on_match: warnOnMatch })
  },
}

// ============ Games API ============

export const gamesToggleApi = {
  /**
   * Get games configuration
   */
  async getConfig(groupId: number): Promise<{
    enabled: boolean
    awardXp: boolean
    awardCoins: boolean
    enabledGames: string[]
  }> {
    const response = await api.get(`/groups/${groupId}/games/config`)
    return response.data
  },

  /**
   * Toggle games module
   */
  async toggle(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/games`, { enabled })
  },

  /**
   * Toggle specific game
   */
  async toggleGame(groupId: number, gameType: string, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/games/${gameType}`, { enabled })
  },

  /**
   * Set rewards
   */
  async setRewards(groupId: number, awardXp: boolean, awardCoins: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/games/rewards`, { award_xp: awardXp, award_coins: awardCoins })
  },

  /**
   * Start a game
   */
  async startGame(groupId: number, gameType: string, options?: Record<string, any>): Promise<{ success: boolean; gameId?: string }> {
    const response = await api.post(`/groups/${groupId}/games/start`, { game_type: gameType, options })
    return response.data
  },
}

// ============ Economy API ============

export const economyToggleApi = {
  /**
   * Get economy configuration
   */
  async getConfig(groupId: number): Promise<{
    enabled: boolean
    currencyName: string
    currencyEmoji: string
    earnPerMessage: number
    earnPerReaction: number
    dailyBonus: number
  }> {
    const response = await api.get(`/groups/${groupId}/economy/config`)
    return response.data
  },

  /**
   * Toggle economy
   */
  async toggle(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/economy`, { enabled })
  },

  /**
   * Set currency settings
   */
  async setCurrency(groupId: number, name: string, emoji: string): Promise<void> {
    await api.patch(`/groups/${groupId}/economy/currency`, { name, emoji })
  },

  /**
   * Set earn rates
   */
  async setEarnRates(groupId: number, perMessage: number, perReaction: number, dailyBonus: number): Promise<void> {
    await api.patch(`/groups/${groupId}/economy/earn-rates`, {
      per_message: perMessage,
      per_reaction: perReaction,
      daily_bonus: dailyBonus,
    })
  },

  /**
   * Get leaderboard
   */
  async getLeaderboard(groupId: number): Promise<Array<{ userId: number; name: string; balance: number }>> {
    const response = await api.get(`/groups/${groupId}/economy/leaderboard`)
    return response.data
  },
}

// ============ Scheduler API ============

export const schedulerToggleApi = {
  /**
   * Get all scheduled messages
   */
  async getMessages(groupId: number): Promise<Array<{
    id: number
    content: string
    scheduleType: string
    nextRun: string
    isEnabled: boolean
  }>> {
    const response = await api.get(`/groups/${groupId}/scheduler/messages`)
    return response.data
  },

  /**
   * Create scheduled message
   */
  async createMessage(groupId: number, data: {
    content: string
    scheduleType: string
    runAt?: string
    cronExpression?: string
    daysOfWeek?: number[]
    timeSlot?: string
  }): Promise<{ id: number }> {
    const response = await api.post(`/groups/${groupId}/scheduler/messages`, data)
    return response.data
  },

  /**
   * Toggle scheduled message
   */
  async toggleMessage(groupId: number, messageId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/scheduler/messages/${messageId}`, { is_enabled: enabled })
  },

  /**
   * Delete scheduled message
   */
  async deleteMessage(groupId: number, messageId: number): Promise<void> {
    await api.delete(`/groups/${groupId}/scheduler/messages/${messageId}`)
  },
}

// ============ Notes & Filters API ============

export const notesFiltersToggleApi = {
  /**
   * Get all notes
   */
  async getNotes(groupId: number): Promise<Array<{
    id: number
    keyword: string
    content: string
    isPrivate: boolean
  }>> {
    const response = await api.get(`/groups/${groupId}/notes`)
    return response.data
  },

  /**
   * Create note
   */
  async createNote(groupId: number, keyword: string, content: string, isPrivate: boolean = false): Promise<void> {
    await api.post(`/groups/${groupId}/notes`, { keyword, content, is_private: isPrivate })
  },

  /**
   * Delete note
   */
  async deleteNote(groupId: number, keyword: string): Promise<void> {
    await api.delete(`/groups/${groupId}/notes/${encodeURIComponent(keyword)}`)
  },

  /**
   * Get all filters
   */
  async getFilters(groupId: number): Promise<Array<{
    id: number
    trigger: string
    matchType: string
    responseContent: string
    action?: string
  }>> {
    const response = await api.get(`/groups/${groupId}/filters`)
    return response.data
  },

  /**
   * Create filter
   */
  async createFilter(groupId: number, data: {
    trigger: string
    matchType: string
    responseContent: string
    action?: string
    deleteTrigger?: boolean
  }): Promise<void> {
    await api.post(`/groups/${groupId}/filters`, data)
  },

  /**
   * Delete filter
   */
  async deleteFilter(groupId: number, filterId: number): Promise<void> {
    await api.delete(`/groups/${groupId}/filters/${filterId}`)
  },
}

// ============ Group Settings API ============

export const groupSettingsApi = {
  /**
   * Get group settings
   */
  async getSettings(groupId: number): Promise<{
    language: string
    timezone: string
    commandPrefix: string
    logChannel?: number
  }> {
    const response = await api.get(`/groups/${groupId}/settings`)
    return response.data
  },

  /**
   * Update settings
   */
  async updateSettings(groupId: number, settings: {
    language?: string
    timezone?: string
    commandPrefix?: string
    logChannel?: number
  }): Promise<void> {
    await api.patch(`/groups/${groupId}/settings`, settings)
  },

  /**
   * Export group data
   */
  async exportData(groupId: number, modules?: string[]): Promise<{ jobId: string }> {
    const response = await api.post(`/groups/${groupId}/export`, { modules })
    return response.data
  },

  /**
   * Import group data
   */
  async importData(groupId: number, data: Record<string, any>): Promise<void> {
    await api.post(`/groups/${groupId}/import`, data)
  },
}

// ============ AI Assistant API ============

export const aiAssistantToggleApi = {
  /**
   * Get AI configuration
   */
  async getConfig(groupId: number): Promise<{
    enabled: boolean
    respondToMentions: boolean
    respondToCommands: boolean
    summarization: boolean
    translation: boolean
    factCheck: boolean
    scamDetection: boolean
  }> {
    const response = await api.get(`/groups/${groupId}/ai-assistant/config`)
    return response.data
  },

  /**
   * Toggle AI assistant
   */
  async toggle(groupId: number, enabled: boolean): Promise<void> {
    await api.patch(`/groups/${groupId}/ai-assistant`, { enabled })
  },

  /**
   * Update AI features
   */
  async updateFeatures(groupId: number, features: Record<string, boolean>): Promise<void> {
    await api.patch(`/groups/${groupId}/ai-assistant/features`, features)
  },
}

export default {
  toggleApi,
  quickActionsApi,
  locksToggleApi,
  antispamToggleApi,
  welcomeToggleApi,
  captchaToggleApi,
  moderationToggleApi,
  rulesToggleApi,
  silentModeApi,
  memberBoosterApi,
  wordFilterApi,
  gamesToggleApi,
  economyToggleApi,
  schedulerToggleApi,
  notesFiltersToggleApi,
  groupSettingsApi,
  aiAssistantToggleApi,
}
