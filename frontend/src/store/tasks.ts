import { create } from 'zustand'

export interface Task {
  task_id: string
  title: string
  description: string
  task_type: string
  mode: 'quick' | 'scheduled'
  urgency_level: number
  status: 'created' | 'assigned' | 'accepted' | 'in_progress' | 'completed' | 'cancelled'
  customer_id: string
  assigned_worker_id?: string
  location_lat: number
  location_lng: number
  estimated_price: number
  actual_price?: number
  created_at: string
  updated_at: string
}

interface TaskState {
  tasks: Task[]
  activeTask: Task | null
  isLoading: boolean
  setTasks: (tasks: Task[]) => void
  setActiveTask: (task: Task | null) => void
  addTask: (task: Task) => void
  updateTask: (taskId: string, updates: Partial<Task>) => void
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  activeTask: null,
  isLoading: false,
  
  setTasks: (tasks: Task[]) => set({ tasks }),
  
  setActiveTask: (task: Task | null) => set({ activeTask: task }),
  
  addTask: (task: Task) => set((state) => ({
    tasks: [task, ...state.tasks]
  })),
  
  updateTask: (taskId: string, updates: Partial<Task>) => set((state) => ({
    tasks: state.tasks.map((task) =>
      task.task_id === taskId ? { ...task, ...updates } : task
    ),
    activeTask: state.activeTask?.task_id === taskId
      ? { ...state.activeTask, ...updates }
      : state.activeTask,
  })),
}))
