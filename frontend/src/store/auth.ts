import { create } from 'zustand'
import { supabase, User } from '@/lib/supabase'

interface AuthState {
  user: User | null
  accessToken: string | null
  loading: boolean
  initialized: boolean
  signIn: (email: string, password: string) => Promise<{ error?: string }>
  signOut: () => Promise<void>
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  loading: false,
  initialized: false,

  initialize: async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        set({
          user: session.user as User,
          accessToken: session.access_token,
          initialized: true,
        })
      } else {
        set({ initialized: true })
      }
    } catch (error) {
      console.error('Auth init error:', error)
      set({ initialized: true })
    }

    // Listen for auth changes
    supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        set({
          user: session.user as User,
          accessToken: session.access_token,
        })
      } else {
        set({ user: null, accessToken: null })
      }
    })
  },

  signIn: async (email: string, password: string) => {
    set({ loading: true })
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        set({ loading: false })
        return { error: error.message }
      }

      set({
        user: data.user as User,
        accessToken: data.session?.access_token || null,
        loading: false,
      })

      return {}
    } catch (error: any) {
      set({ loading: false })
      return { error: error.message || 'Sign in failed' }
    }
  },

  signOut: async () => {
    await supabase.auth.signOut()
    set({ user: null, accessToken: null })
  },
}))
