import apiClient from './api'
import type { AuthUser as User } from '@/types'

export const authService = {
  registerCustomer: async (userData: Partial<User> & { password?: string }) => {
    const response = await apiClient.post('/auth/register/customer', userData)
    return response.data
  },

  registerWorker: async (userData: Partial<User> & { service_types: string[]; location_lat: number; location_lng: number }) => {
    const response = await apiClient.post('/auth/register/worker', userData)
    return response.data
  },

  login: async (phoneNumber: string, password: string) => {
    const response = await apiClient.post('/auth/login', { phone_number: phoneNumber, password })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}
