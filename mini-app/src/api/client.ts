import axios from 'axios'

// Production API URL - Your Render deployment
const PRODUCTION_API_URL = 'https://nexus-4uxn.onrender.com'

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
  const token = localStorage.getItem('nexus_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    // Log first few chars of token for debugging
    console.log('[API Client] Adding token:', token.substring(0, 20) + '...')
  } else {
    console.log('[API Client] No token found in localStorage')
  }
  return config
})

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Client] Response error:', error.response?.status, error.response?.data)
    if (error.response?.status === 401) {
      localStorage.removeItem('nexus_token')
      // Only reload if not already on auth page to avoid loops
      if (!window.location.pathname.includes('/auth')) {
        window.location.reload()
      }
    }
    return Promise.reject(error)
  }
)

export default api
