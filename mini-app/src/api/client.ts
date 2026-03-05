import axios from 'axios'

// Import both debug systems for enhanced logging
import {
  enhancedDebug,
  telegramDebug,
  ErrorAnalyzer,
  LogCategory,
  LogLevel,
} from '../utils/enhancedDebug'

// Backward compatibility
import {
  debugLog,
  logApiRequest,
  logApiResponse,
  logToken,
} from '../utils/debug'

// Production API URL - Your Render deployment
const PRODUCTION_API_URL = 'https://nexus-4uxn.onrender.com'

// Track if we've already handled a 401 to prevent reload loops
let hasHandled401 = false

// Detect the API URL based on environment
const getApiUrl = (): string => {
  enhancedDebug.debug('API URL Detection Start', LogCategory.API);

  // Check for environment variable (set at build time)
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== 'http://localhost:8000') {
    enhancedDebug.debug('Using VITE_API_URL', LogCategory.API, { url: import.meta.env.VITE_API_URL });
    return import.meta.env.VITE_API_URL
  }

  // If running in browser, use the same origin as the current page
  if (typeof window !== 'undefined' && window.location.origin) {
    const origin = window.location.origin
    enhancedDebug.debug('Using window.location.origin', LogCategory.API, { origin });

    // Don't use file:// or invalid origins
    if (origin !== 'file://' && origin.startsWith('http')) {
      return origin
    }
  }

  // Default to production API URL
  enhancedDebug.debug('Using default PRODUCTION_API_URL', LogCategory.API, { url: PRODUCTION_API_URL });
  return PRODUCTION_API_URL
}

const API_BASE_URL = getApiUrl()

enhancedDebug.info('API Client initialized', LogCategory.API, { baseUrl: `${API_BASE_URL}/api/v1` });

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  telegramDebug.logApiCall(config.method?.toUpperCase() || 'GET', config.url || '', config.data);

  // Always read fresh from localStorage to avoid stale closures
  const token = localStorage.getItem('nexus_token')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    enhancedDebug.debug('Token added to request', LogCategory.TOKEN, {
      url: config.url,
      tokenPreview: token.substring(0, 20) + '...',
    });
  } else {
    enhancedDebug.warn(`No token found for request to ${config.url}`, LogCategory.TOKEN);

    // Enhanced debug: Check Telegram context
    const tg = (window as any).Telegram?.WebApp
    if (!tg) {
      enhancedDebug.warn('Not running in Telegram WebApp context', LogCategory.TELEGRAM);
    } else if (!tg.initData) {
      enhancedDebug.warn('Telegram WebApp exists but no initData', LogCategory.TELEGRAM, {
        explanation: 'May be in private chat or still loading',
        workarounds: ['Wait for initData', 'Open from a group instead'],
      });
    } else {
      enhancedDebug.debug('initData exists but no token - auth may be in progress', LogCategory.TELEGRAM);
    }
  }

  // Log full request details (backward compatibility)
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
    telegramDebug.logApiResponse(
      response.config.method?.toUpperCase() || 'GET',
      response.config.url || '',
      response.status,
      response.data
    );

    // Backward compatibility
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

    // Analyze the error for better diagnostics
    const errorAnalysis = ErrorAnalyzer.analyze(error, { url, method, status });

    enhancedDebug.error(
      `API Error: ${method} ${url} - ${status}`,
      error,
      LogCategory.API,
      {
        status,
        url,
        method,
        errorData: error.response?.data,
        analysis: errorAnalysis,
      }
    );

    if (status === 401) {
      if (hasHandled401) {
        enhancedDebug.debug('401 already handled, skipping reload', LogCategory.AUTH);
        return Promise.reject(error)
      }

      hasHandled401 = true
      enhancedDebug.warn('401 received, clearing token', LogCategory.AUTH);
      localStorage.removeItem('nexus_token')

      // Check if we have valid Telegram initData
      const tg = (window as any).Telegram?.WebApp
      const hasValidInitData = tg?.initData && tg?.initData.length > 0

      if (!hasValidInitData) {
        enhancedDebug.error(
          'Cannot re-authenticate: Not in Telegram context',
          new Error('No initData available'),
          LogCategory.AUTH,
          {
            fix: 'Reload the page in Telegram WebApp context or log in again',
            workarounds: [
              'Open Mini App from Telegram group',
              'Check if session expired',
              'Clear browser storage and retry',
            ],
          }
        );

        window.dispatchEvent(new CustomEvent('nexus:authFailed', {
          detail: {
            reason: 'not_in_telegram',
            fix: 'Open Mini App from a Telegram group',
          }
        }))
      } else {
        enhancedDebug.info('Valid initData found, scheduling reload', LogCategory.AUTH);
        setTimeout(() => {
          if (!window.location.pathname.includes('/auth')) {
            enhancedDebug.info('Reloading page due to 401', LogCategory.AUTH);
            window.location.reload()
          }
        }, 500)
      }
    }

    // Network errors
    if (!error.response) {
      enhancedDebug.error(
        'Network error - no response received',
        error,
        LogCategory.NETWORK,
        {
          fix: 'Check internet connection and API server status',
          url,
          method,
        }
      );
    }

    return Promise.reject(error)
  }
)

export default api
