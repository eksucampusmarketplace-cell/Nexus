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
  token: string | null
  user: User | null
  error: string | null
  setAuth: (token: string, user: User) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  logout: () => void
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
    }),
    {
      name: 'nexus-auth',
    }
  )
)
