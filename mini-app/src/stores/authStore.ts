import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { debugLog, LogCategory, LogLevel, logToken, logStorage, logAuthState } from '../utils/debug'

export interface User {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  language_code: string
  is_premium: boolean
  is_owner: boolean
  is_support: boolean
  is_staff: boolean
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
  // Check if current user is owner/support
  isUserOwner: () => boolean
  isUserSupport: () => boolean
  isUserStaff: () => boolean
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
        debugLog(LogCategory.AUTH, '=== SET AUTH CALLED ===', null);
        debugLog(LogCategory.AUTH, 'Setting authenticated user:', {
          userId: user.id,
          telegramId: user.telegram_id,
          username: user.username,
          isOwner: user.is_owner,
          isSupport: user.is_support,
        });
        
        // Ensure token is written to localStorage BEFORE state update
        debugLog(LogCategory.STORAGE, 'Writing token to localStorage', token.substring(0, 30) + '...');
        localStorage.setItem('nexus_token', token)
        logStorage('set', 'nexus_token', token.substring(0, 30) + '...');
        logToken('stored', token);
        
        set({ isAuthenticated: true, token, user, error: null })
        debugLog(LogCategory.AUTH, 'Auth state updated - isAuthenticated: true', null);
        logAuthState('store_updated_authenticated');
      },
      setLoading: (loading) => {
        debugLog(LogCategory.AUTH, `Setting loading state: ${loading}`, null);
        set({ isLoading: loading })
      },
      setError: (error) => {
        debugLog(LogCategory.AUTH, `Setting error state:`, error, LogLevel.ERROR);
        set({ error })
      },
      logout: () => {
        debugLog(LogCategory.AUTH, '=== LOGOUT CALLED ===', null);
        logAuthState('logging_out');
        
        debugLog(LogCategory.STORAGE, 'Removing token from localStorage', null);
        localStorage.removeItem('nexus_token')
        logStorage('remove', 'nexus_token');
        logToken('cleared');
        
        set({ isAuthenticated: false, token: null, user: null })
        debugLog(LogCategory.AUTH, 'Auth state cleared', null);
        logAuthState('logged_out');
      },
      hasStoredToken: () => {
        const hasToken = !!localStorage.getItem('nexus_token')
        debugLog(LogCategory.STORAGE, `Checking for stored token: ${hasToken}`, null);
        return hasToken
      },
      isAuthReady: () => {
        const state = get()
        const ready = state.isRehydrated && !state.isLoading
        debugLog(LogCategory.AUTH, `isAuthReady check: rehydrated=${state.isRehydrated}, loading=${state.isLoading}, ready=${ready}`, null);
        return ready
      },
      isUserOwner: () => {
        const state = get()
        const isOwner = state.user?.is_owner ?? false
        debugLog(LogCategory.USER, `isUserOwner check: ${isOwner}`, null);
        return isOwner
      },
      isUserSupport: () => {
        const state = get()
        const isSupport = state.user?.is_support ?? false
        debugLog(LogCategory.USER, `isUserSupport check: ${isSupport}`, null);
        return isSupport
      },
      isUserStaff: () => {
        const state = get()
        const isStaff = state.user?.is_staff ?? false
        debugLog(LogCategory.USER, `isUserStaff check: ${isStaff}`, null);
        return isStaff
      }
    }),
    {
      name: 'nexus-auth',
      onRehydrateStorage: () => (state) => {
        debugLog(LogCategory.STORAGE, '=== STORE REHYDRATION ===', null);
        // Mark as rehydrated after persist middleware restores state
        if (state) {
          debugLog(LogCategory.STORAGE, 'Store rehydrated with state:', {
            isAuthenticated: state.isAuthenticated,
            hasToken: !!state.token,
            hasUser: !!state.user,
          });
          state.isRehydrated = true
          logAuthState('store_rehydrated');
        } else {
          debugLog(LogCategory.STORAGE, 'Store rehydrated with no state (first visit)', null);
        }
      }
    }
  )
)
