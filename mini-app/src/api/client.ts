import axios from 'axios'

// Detect the API URL based on environment
const getApiUrl = () => {
  // Check for environment variable (set at build time)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // If running on the same domain (served from API service), use current origin
  if (typeof window !== 'undefined' && window.location.origin) {
    // Check if we're on the API service domain
    if (window.location.hostname.includes('nexus-4uxn.onrender.com') || 
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1') {
      return window.location.origin
    }
  }
  
  // Fallback to production API URL
  return 'https://nexus-4uxn.onrender.com'
}

const API_BASE_URL = getApiUrl()

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
  }
  return config
})

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('nexus_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default api
