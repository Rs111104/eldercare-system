import axios, { type AxiosError, type AxiosResponse } from 'axios'
import { useStore } from '@/store/useStore'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = useStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<{ detail?: unknown; message?: unknown }>) => {
    const status = error.response?.status
    if (status === 401) {
      useStore.getState().logout()
    }
    const message = error.response?.data?.detail || error.response?.data?.message || 'Something went wrong. Please try again.'
    const err = new Error(typeof message === 'string' ? message : JSON.stringify(message))
    return Promise.reject(err)
  },
)

export default client
