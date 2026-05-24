import apiClient from './api'
import { Task } from '@/store/tasks'

export const taskService = {
  createTask: async (taskData: Omit<Task, 'task_id' | 'created_at' | 'updated_at'>) => {
    const response = await apiClient.post('/tasks/create', taskData)
    return response.data
  },

  getTask: async (taskId: string) => {
    const response = await apiClient.get(`/tasks/${taskId}`)
    return response.data
  },

  updateTask: async (taskId: string, updates: Partial<Task>) => {
    const response = await apiClient.put(`/tasks/${taskId}`, updates)
    return response.data
  },

  getCustomerTasks: async (customerId: string) => {
    const response = await apiClient.get(`/tasks/customer/${customerId}`)
    return response.data
  },

  getAvailableQuickTasks: async () => {
    const response = await apiClient.get('/tasks/available/quick')
    return response.data
  },
}
