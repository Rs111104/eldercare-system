export type Role = 'customer' | 'worker' | 'admin'

export interface AuthUser {
  id: string
  phone: string
  phone_number?: string
  name: string
  role: Role
  service_type?: string
  rating?: number
  is_verified?: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user_id: string
  user_type: Role
  user: AuthUser
}

export interface Task {
  id: string
  task_id?: string
  title: string
  customer_id: string
  worker_id?: string | null
  assigned_worker_id?: string | null
  service_type: string
  task_type?: string
  status: string
  description: string
  price: number
  urgency: number
  urgency_level?: number
  voice_note_url?: string | null
  created_at: string
  completed_at?: string | null
  matched_workers?: Worker[]
}

export interface Worker {
  id: string
  worker_id?: string
  phone: string
  phone_number?: string
  name: string
  service_type: string
  service_types?: string[]
  rating: number
  is_verified: boolean
  current_lat?: number | null
  current_lng?: number | null
  distance_km?: number
  created_at: string
}

export interface Customer {
  id: string
  phone: string
  name: string
  address: string
  lat?: number | null
  lng?: number | null
  created_at: string
}

export interface PricingEstimate {
  service_type: string
  base_price: number
  distance_km: number
  urgency: number
  urgency_multiplier: number
  total_price: number
}

export interface Payout {
  id: string
  worker_id: string
  task_id: string
  amount: number
  split_type: 'immediate' | 'verification'
  status: string
  released_at?: string | null
}

export interface StatsOverview {
  total_customers: number
  total_workers: number
  verified_workers: number
  total_tasks: number
  completed_tasks: number
  total_payouts: number
  total_revenue: number
  average_rating: number
}

export interface AppError {
  message: string
}
