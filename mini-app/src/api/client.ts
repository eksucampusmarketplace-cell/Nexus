import axios from 'axios'

// Production API URL - Your Render deployment
const PRODUCTION_API_URL = 'https://nexus-4uxn.onrender.com'

// Track if we've already handled a 401 to prevent reload loops
let hasHandled401 = false

// Detect the API URL based on environment
const getApiUrl = (): string => {
  // Check for environment variable (set at build time)
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL !== 'http://localhost:8000') {
    console.log('[API Client] Using VITE_API_URL:', import.meta.env.VITE_API_URL)
    return import.meta.env.VITE_API_URL
  }

  // If running in browser, use the same origin as the current page
  // This ensures the mini-app and API are always on the same domain
  if (typeof window !== 'undefined' && window.location.origin) {
    const origin = window.location.origin
    console.log('[API Client] Using window.location.origin:', origin)
    
    // Don't use file:// or invalid origins
    if (origin !== 'file://' && origin.startsWith('http')) {
      return origin
    }
  }

  // Default to production API URL
  console.log('[API Client] Using default PRODUCTION_API_URL:', PRODUCTION_API_URL)
  return PRODUCTION_API_URL
}

const API_BASE_URL = getApiUrl()

console.log('[API Client] Initialized with base URL:', `${API_BASE_URL}/api/v1`)

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  // Always read fresh from localStorage to avoid stale closures
  const token = localStorage.getItem('nexus_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    // Log first few chars of token for debugging
    console.log(`[API Client] Adding token to ${config.url}:`, token.substring(0, 20) + '...')
  } else {
    console.log(`[API Client] No token found for request to ${config.url}`)
    // Debug: Check if we're in Telegram context
    const tg = (window as any).Telegram?.WebApp
    if (!tg) {
      console.log('[API Client] Not running in Telegram WebApp context')
    } else if (!tg.initData) {
      console.log('[API Client] Telegram WebApp exists but no initData')
    }
  }
  return config
})

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url
    
    console.error(`[API Client] Response error for ${url}:`, status, error.response?.data)
    
    if (status === 401) {
      // Only handle 401 once to prevent reload loops
      if (hasHandled401) {
        console.log('[API Client] 401 already handled, skipping reload')
        return Promise.reject(error)
      }
      
      hasHandled401 = true
      console.log('[API Client] 401 received, clearing token')
      localStorage.removeItem('nexus_token')
      
      // Check if we have valid Telegram initData - if not, we can't re-auth
      const tg = (window as any).Telegram?.WebApp
      const hasValidInitData = tg?.initData && tg?.initData.length > 0
      
      if (!hasValidInitData) {
        // Not in Telegram context - can't re-authenticate, show error
        console.log('[API Client] Not in Telegram context, cannot re-authenticate')
        // Dispatch a custom event so the app can show appropriate error
        window.dispatchEvent(new CustomEvent('nexus:authFailed', { 
          detail: { reason: 'not_in_telegram' } 
        }))
      } else {
        // Delay reload slightly to prevent rapid loops
        setTimeout(() => {
          // Only reload if not already on auth page to avoid loops
          if (!window.location.pathname.includes('/auth')) {
            console.log('[API Client] Reloading page due to 401')
            window.location.reload()
          }
        }, 500)
      }
    }
    return Promise.reject(error)
  }
)

export default api
