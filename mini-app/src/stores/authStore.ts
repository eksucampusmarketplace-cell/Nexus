import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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
  isRehydrated: boolean
  token: string | null
  user: User | null
  error: string | null
  setAuth: (token: string, user: User) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  logout: () => void
  // Helper to check if we have a stored token
  hasStoredToken: () => boolean
  // Check if auth is ready (rehydrated and not loading)
  isAuthReady: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      isLoading: true,
      isRehydrated: false,
      token: null,
      user: null,
      error: null,
      setAuth: (token, user) => {
        // Ensure token is written to localStorage BEFORE state update
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
      },
      isAuthReady: () => {
        const state = get()
        return state.isRehydrated && !state.isLoading
      }
    }),
    {
      name: 'nexus-auth',
      onRehydrateStorage: () => (state) => {
        // Mark as rehydrated after persist middleware restores state
        if (state) {
          state.isRehydrated = true
        }
      }
    }
  )
)
