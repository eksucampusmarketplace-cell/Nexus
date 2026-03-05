/**
 * Debug Logger Utility
 * 
 * Provides comprehensive logging for all Telegram-WebApp communication
 */

// Enable all debug logging
const DEBUG_ENABLED = true;

// Log levels
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

// Categories for filtering
export enum LogCategory {
  TELEGRAM = 'TELEGRAM',
  AUTH = 'AUTH',
  API = 'API',
  WEBSOCKET = 'WS',
  STORAGE = 'STORAGE',
  HASH = 'HASH',
  INIT = 'INIT',
  TOKEN = 'TOKEN',
  GROUPS = 'GROUPS',
  USER = 'USER',
}

// Color codes for console
const colors: Record<LogCategory, string> = {
  [LogCategory.TELEGRAM]: '#00bcd4', // Cyan
  [LogCategory.AUTH]: '#4caf50', // Green
  [LogCategory.API]: '#2196f3', // Blue
  [LogCategory.WEBSOCKET]: '#ff9800', // Orange
  [LogCategory.STORAGE]: '#9c27b0', // Purple
  [LogCategory.HASH]: '#f44336', // Red
  [LogCategory.INIT]: '#ffeb3b', // Yellow
  [LogCategory.TOKEN]: '#e91e63', // Pink
  [LogCategory.GROUPS]: '#795548', // Brown
  [LogCategory.USER]: '#607d8b', // Gray
};

/**
 * Main debug logger function
 */
export function debugLog(
  category: LogCategory,
  message: string,
  data?: any,
  level: LogLevel = LogLevel.DEBUG
) {
  if (!DEBUG_ENABLED) return;

  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level}] [${category}]`;
  const color = colors[category] || '#fff';

  // Style based on level
  let logFn = console.log;
  if (level === LogLevel.ERROR) logFn = console.error;
  if (level === LogLevel.WARN) logFn = console.warn;

  // Log with colored category
  logFn(
    `%c${prefix}%c ${message}`,
    `color: ${color}; font-weight: bold;`,
    'color: inherit;',
    data !== undefined ? data : ''
  );

  // Also log to session storage for persistence (limited to last 100 entries)
  try {
    const logEntry = { timestamp, category, level, message, data };
    const existing = sessionStorage.getItem('nexus_debug_log');
    const logs = existing ? JSON.parse(existing) : [];
    logs.push(logEntry);
    if (logs.length > 100) logs.shift();
    sessionStorage.setItem('nexus_debug_log', JSON.stringify(logs));
  } catch (e) {
    // Ignore storage errors
  }
}

/**
 * Log Telegram WebApp events
 */
export function logTelegramEvent(event: string, data?: any) {
  debugLog(LogCategory.TELEGRAM, `Event: ${event}`, data, LogLevel.INFO);
}

/**
 * Log Telegram WebApp init data
 */
export function logInitData(tg: any) {
  debugLog(LogCategory.INIT, '=== TELEGRAM WEBAPP INIT DATA DUMP ===', null, LogLevel.INFO);
  
  if (!tg) {
    debugLog(LogCategory.INIT, 'Telegram WebApp object is NULL/UNDEFINED', null, LogLevel.ERROR);
    return;
  }

  // Log all WebApp properties
  debugLog(LogCategory.INIT, 'WebApp.version:', tg.version, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'WebApp.platform:', tg.platform, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'WebApp.colorScheme:', tg.colorScheme, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'WebApp.isExpanded:', tg.isExpanded, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'WebApp.viewportHeight:', tg.viewportHeight, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'WebApp.viewportStableHeight:', tg.viewportStableHeight, LogLevel.INFO);
  
  // Init data
  debugLog(LogCategory.INIT, '=== INIT DATA ===', null, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'initData exists:', !!tg.initData, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'initData length:', tg.initData?.length || 0, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'initData raw (first 500 chars):', tg.initData?.substring(0, 500), LogLevel.INFO);
  
  // Init data unsafe
  debugLog(LogCategory.INIT, '=== INIT DATA UNSAFE ===', null, LogLevel.INFO);
  debugLog(LogCategory.INIT, 'initDataUnsafe exists:', !!tg.initDataUnsafe, LogLevel.INFO);
  
  if (tg.initDataUnsafe) {
    debugLog(LogCategory.INIT, 'initDataUnsafe.user:', tg.initDataUnsafe.user, LogLevel.INFO);
    debugLog(LogCategory.INIT, 'initDataUnsafe.chat:', tg.initDataUnsafe.chat, LogLevel.INFO);
    debugLog(LogCategory.INIT, 'initDataUnsafe.start_param:', tg.initDataUnsafe.start_param, LogLevel.INFO);
    debugLog(LogCategory.INIT, 'initDataUnsafe.auth_date:', tg.initDataUnsafe.auth_date, LogLevel.INFO);
    debugLog(LogCategory.INIT, 'initDataUnsafe.hash:', tg.initDataUnsafe.hash ? `${tg.initDataUnsafe.hash.substring(0, 20)}...` : 'missing', LogLevel.INFO);
    debugLog(LogCategory.INIT, 'initDataUnsafe.query_id:', tg.initDataUnsafe.query_id, LogLevel.INFO);
    
    // User details
    if (tg.initDataUnsafe.user) {
      debugLog(LogCategory.USER, '=== USER DATA ===', null, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.id:', tg.initDataUnsafe.user.id, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.username:', tg.initDataUnsafe.user.username, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.first_name:', tg.initDataUnsafe.user.first_name, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.last_name:', tg.initDataUnsafe.user.last_name, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.language_code:', tg.initDataUnsafe.user.language_code, LogLevel.INFO);
      debugLog(LogCategory.USER, 'user.is_premium:', tg.initDataUnsafe.user.is_premium, LogLevel.INFO);
    }
    
    // Chat details
    if (tg.initDataUnsafe.chat) {
      debugLog(LogCategory.GROUPS, '=== CHAT DATA ===', null, LogLevel.INFO);
      debugLog(LogCategory.GROUPS, 'chat.id:', tg.initDataUnsafe.chat.id, LogLevel.INFO);
      debugLog(LogCategory.GROUPS, 'chat.type:', tg.initDataUnsafe.chat.type, LogLevel.INFO);
      debugLog(LogCategory.GROUPS, 'chat.title:', tg.initDataUnsafe.chat.title, LogLevel.INFO);
      debugLog(LogCategory.GROUPS, 'chat.username:', tg.initDataUnsafe.chat.username, LogLevel.INFO);
    }
  }
  
  debugLog(LogCategory.INIT, '=== END INIT DATA DUMP ===', null, LogLevel.INFO);
}

/**
 * Log hash computation details
 */
export function logHashComputation(
  initData: string,
  botTokenHint: string,
  computedHash?: string,
  receivedHash?: string,
  match?: boolean
) {
  debugLog(LogCategory.HASH, '=== HASH COMPUTATION ===', null, LogLevel.INFO);
  debugLog(LogCategory.HASH, 'initData length:', initData?.length, LogLevel.INFO);
  debugLog(LogCategory.HASH, 'initData (first 300 chars):', initData?.substring(0, 300), LogLevel.INFO);
  debugLog(LogCategory.HASH, 'bot token hint:', botTokenHint, LogLevel.INFO);
  debugLog(LogCategory.HASH, 'computed hash:', computedHash ? `${computedHash.substring(0, 20)}...` : 'none', LogLevel.INFO);
  debugLog(LogCategory.HASH, 'received hash:', receivedHash ? `${receivedHash.substring(0, 20)}...` : 'none', LogLevel.INFO);
  debugLog(LogCategory.HASH, 'hash match:', match, match ? LogLevel.INFO : LogLevel.ERROR);
  debugLog(LogCategory.HASH, '=== END HASH COMPUTATION ===', null, LogLevel.INFO);
}

/**
 * Log API request
 */
export function logApiRequest(method: string, url: string, data?: any, headers?: any) {
  debugLog(LogCategory.API, `REQUEST: ${method} ${url}`, null, LogLevel.INFO);
  if (data) {
    // Don't log sensitive data like full init_data in production
    const sanitized = { ...data };
    if (sanitized.init_data) {
      sanitized.init_data = `${sanitized.init_data.substring(0, 50)}... (${sanitized.init_data.length} chars)`;
    }
    debugLog(LogCategory.API, 'Request body:', sanitized, LogLevel.DEBUG);
  }
  if (headers) {
    const sanitizedHeaders = { ...headers };
    if (sanitizedHeaders.Authorization) {
      sanitizedHeaders.Authorization = 'Bearer ***';
    }
    debugLog(LogCategory.API, 'Request headers:', sanitizedHeaders, LogLevel.DEBUG);
  }
}

/**
 * Log API response
 */
export function logApiResponse(method: string, url: string, status: number, data?: any) {
  debugLog(LogCategory.API, `RESPONSE: ${method} ${url} - Status: ${status}`, null, LogLevel.INFO);
  if (data && status >= 400) {
    debugLog(LogCategory.API, 'Error response:', data, LogLevel.ERROR);
  }
}

/**
 * Log WebSocket events
 */
export function logWebSocket(event: string, data?: any) {
  debugLog(LogCategory.WEBSOCKET, `WS ${event}`, data, LogLevel.INFO);
}

/**
 * Log storage operations
 */
export function logStorage(operation: 'get' | 'set' | 'remove', key: string, value?: any) {
  const sanitized = key === 'nexus_token' && value ? '***token***' : value;
  debugLog(LogCategory.STORAGE, `Storage ${operation.toUpperCase()}: ${key}`, sanitized, LogLevel.DEBUG);
}

/**
 * Log auth state changes
 */
export function logAuthState(state: string, details?: any) {
  debugLog(LogCategory.AUTH, `Auth state: ${state}`, details, LogLevel.INFO);
}

/**
 * Log token operations
 */
export function logToken(operation: string, tokenHint?: string) {
  debugLog(LogCategory.TOKEN, `Token ${operation}`, tokenHint ? `${tokenHint.substring(0, 20)}...` : null, LogLevel.INFO);
}

/**
 * Get all stored logs
 */
export function getStoredLogs() {
  try {
    const logs = sessionStorage.getItem('nexus_debug_log');
    return logs ? JSON.parse(logs) : [];
  } catch (e) {
    return [];
  }
}

/**
 * Clear stored logs
 */
export function clearStoredLogs() {
  try {
    sessionStorage.removeItem('nexus_debug_log');
  } catch (e) {
    // Ignore
  }
}

/**
 * Export logs as formatted text
 */
export function exportLogs(): string {
  const logs = getStoredLogs();
  return logs.map((log: any) => 
    `[${log.timestamp}] [${log.level}] [${log.category}] ${log.message}${log.data ? ' ' + JSON.stringify(log.data) : ''}`
  ).join('\n');
}

export default debugLog;
