import { create } from 'zustand'
import { persist, StateStorage } from 'zustand/middleware'

export interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  language_code: string
  is_premium: boolean
}

interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  token: string | null
  user: User | null
  error: string | null
  setAuth: (token: string, user: User) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  logout: () => void
  // Helper to check if we have a stored token
  hasStoredToken: () => boolean
}

// Custom storage that also syncs the token to nexus_token
const customStorage: StateStorage = {
  getItem: (name: string): string | null => {
    const value = localStorage.getItem(name)
    return value
  },
  setItem: (name: string, value: string): void => {
    // Also sync to nexus_token for the API client
    try {
      const parsed = JSON.parse(value)
      if (parsed.state?.token) {
        localStorage.setItem('nexus_token', parsed.state.token)
      }
    } catch (e) {
      // Ignore parse errors
    }
    localStorage.setItem(name, value)
  },
  removeItem: (name: string): void => {
    if (name === 'nexus-auth') {
      localStorage.removeItem('nexus_token')
    }
    localStorage.removeItem(name)
  },
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      isLoading: true,
      token: null,
      user: null,
      error: null,
      setAuth: (token, user) => {
        localStorage.setItem('nexus_token', token)
        set({ isAuthenticated: true, token, user, error: null })
      },
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      logout: () => {
        localStorage.removeItem('nexus_token')
        set({ isAuthenticated: false, token: null, user: null })
      },
      hasStoredToken: () => {
        return !!localStorage.getItem('nexus_token')
      }
    }),
    {
      name: 'nexus-auth',
      storage: customStorage,
    }
  )
)
