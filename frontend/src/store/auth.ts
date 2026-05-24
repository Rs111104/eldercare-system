import { create } from 'zustand'

export interface User {
  user_id?: string
  worker_id?: string
  phone_number: string
  name: string
  user_type: 'customer' | 'worker' | 'admin'
  email?: string
  profile_picture_url?: string
  service_types?: string[]
  rating?: number
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (user: User, token: string) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user') || '{}') : null,
  token: localStorage.getItem('token'),
  isLoading: false,
  
  login: (user: User, token: string) => {
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('token', token)
    set({ user, token })
  },
  
  logout: () => {
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },
  
  setUser: (user: User) => {
    localStorage.setItem('user', JSON.stringify(user))
    set({ user })
  },
}))
