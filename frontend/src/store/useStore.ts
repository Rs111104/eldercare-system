import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser, Payout, StatsOverview, Task, Worker } from '@/types'

interface AppState {
  user: AuthUser | null
  token: string | null
  tasks: Task[]
  workers: Worker[]
  payouts: Payout[]
  stats: StatsOverview | null
  selectedTaskId: string | null
  isLoading: boolean
  error: string | null
  login: (user: AuthUser, token: string) => void
  logout: () => void
  setTasks: (tasks: Task[]) => void
  setWorkers: (workers: Worker[]) => void
  setPayouts: (payouts: Payout[]) => void
  setStats: (stats: StatsOverview | null) => void
  setSelectedTaskId: (taskId: string | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
}

const initialState = {
  user: null,
  token: null,
  tasks: [],
  workers: [],
  payouts: [],
  stats: null,
  selectedTaskId: null,
  isLoading: false,
  error: null,
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,
      login: (user, token) => set({ user, token, error: null }),
      logout: () => set({ user: null, token: null, tasks: [], workers: [], payouts: [], stats: null, selectedTaskId: null, error: null }),
      setTasks: (tasks) => set({ tasks }),
      setWorkers: (workers) => set({ workers }),
      setPayouts: (payouts) => set({ payouts }),
      setStats: (stats) => set({ stats }),
      setSelectedTaskId: (selectedTaskId) => set({ selectedTaskId }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'eldercare-store',
      partialize: (state) => ({ user: state.user, token: state.token, selectedTaskId: state.selectedTaskId }),
    },
  ),
)
