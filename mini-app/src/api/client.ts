import axios from 'axios'
import { 
  debugLog, 
  LogCategory, 
  LogLevel,
  logApiRequest, 
  logApiResponse,
  logToken,
  logTelegramEvent
} from '../utils/debug'

// Production API URL - Your Render deployment
const PRODUCTION_API_URL = 'https://nexus-4uxn.onrender.com'

// Track if we've already handled a 401 to prevent reload loops
let hasHandled401 = false

// Detect the API URL based on environment
const getApiUrl = (): string => {
  debugLog(LogCategory.API, '=== API URL DETECTION START ===', null);
  
  // Check for environment variable (set at build time)
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== 'http://localhost:8000') {
    debugLog(LogCategory.API, 'Using VITE_API_URL:', import.meta.env.VITE_API_URL);
    return import.meta.env.VITE_API_URL
  }

  // If running in browser, use the same origin as the current page
  // This ensures the mini-app and API are always on the same domain
  if (typeof window !== 'undefined' && window.location.origin) {
    const origin = window.location.origin
    debugLog(LogCategory.API, 'Using window.location.origin:', origin);
    
    // Don't use file:// or invalid origins
    if (origin !== 'file://' && origin.startsWith('http')) {
      return origin
    }
  }

  // Default to production API URL
  debugLog(LogCategory.API, 'Using default PRODUCTION_API_URL:', PRODUCTION_API_URL);
  return PRODUCTION_API_URL
}

const API_BASE_URL = getApiUrl()

debugLog(LogCategory.API, 'API Client initialized with base URL:', `${API_BASE_URL}/api/v1`);

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  debugLog(LogCategory.API, `=== OUTGOING REQUEST: ${config.method?.toUpperCase()} ${config.url} ===`, null);
  
  // Always read fresh from localStorage to avoid stale closures
  const token = localStorage.getItem('nexus_token')
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    logToken('added_to_request', token);
    debugLog(LogCategory.API, `Token added to ${config.url}`, token.substring(0, 20) + '...');
  } else {
    debugLog(LogCategory.TOKEN, `No token found for request to ${config.url}`, null, LogLevel.WARN);
    
    // Debug: Check if we're in Telegram context
    const tg = (window as any).Telegram?.WebApp
    if (!tg) {
      debugLog(LogCategory.TELEGRAM, 'Not running in Telegram WebApp context', null, LogLevel.WARN);
    } else if (!tg.initData) {
      debugLog(LogCategory.TELEGRAM, 'Telegram WebApp exists but no initData (may be in private chat or loading)', null, LogLevel.WARN);
    } else {
      debugLog(LogCategory.TELEGRAM, 'initData exists but no token - auth may be in progress', null);
    }
  }
  
  // Log full request details
  logApiRequest(
    config.method?.toUpperCase() || 'GET',
    config.url || '',
    config.data,
    config.headers as any
  );
  
  return config
})

// Handle response errors
api.interceptors.response.use(
  (response) => {
    debugLog(LogCategory.API, `=== INCOMING RESPONSE: ${response.config.method?.toUpperCase()} ${response.config.url} - Status: ${response.status} ===`, null);
    logApiResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      response.data
    );
    return response
  },
  (error) => {
    const status = error.response?.status
    const url = error.config?.url
    const method = error.config?.method?.toUpperCase()
    
    debugLog(LogCategory.API, `=== RESPONSE ERROR: ${method} ${url} - Status: ${status} ===`, null, LogLevel.ERROR);
    debugLog(LogCategory.API, 'Error response data:', error.response?.data, LogLevel.ERROR);
    debugLog(LogCategory.API, 'Error message:', error.message, LogLevel.ERROR);
    
    if (status === 401) {
      // Only handle 401 once to prevent reload loops
      if (hasHandled401) {
        debugLog(LogCategory.AUTH, '401 already handled, skipping reload', null);
        return Promise.reject(error)
      }
      
      hasHandled401 = true
      debugLog(LogCategory.AUTH, '401 received, clearing token', null);
      localStorage.removeItem('nexus_token')
      logToken('cleared_due_to_401');
      
      // Check if we have valid Telegram initData - if not, we can't re-auth
      const tg = (window as any).Telegram?.WebApp
      const hasValidInitData = tg?.initData && tg?.initData.length > 0
      
      if (!hasValidInitData) {
        // Not in Telegram context - can't re-authenticate, show error
        debugLog(LogCategory.AUTH, 'Not in Telegram context, cannot re-authenticate', null, LogLevel.ERROR);
        // Dispatch a custom event so the app can show appropriate error
        window.dispatchEvent(new CustomEvent('nexus:authFailed', { 
          detail: { reason: 'not_in_telegram' } 
        }))
      } else {
        debugLog(LogCategory.AUTH, 'Valid initData found, scheduling reload', null);
        // Delay reload slightly to prevent rapid loops
        setTimeout(() => {
          // Only reload if not already on auth page to avoid loops
          if (!window.location.pathname.includes('/auth')) {
            debugLog(LogCategory.AUTH, 'Reloading page due to 401', null);
            window.location.reload()
          }
        }, 500)
      }
    }
    return Promise.reject(error)
  }
)

export default api
