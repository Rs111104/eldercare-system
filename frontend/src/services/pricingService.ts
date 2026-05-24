import apiClient from './api'

export const pricingService = {
  calculatePrice: async (factors: {
    distance_km: number
    service_type: string
    effort_level: number
    urgency_multiplier?: number
    travel_time_minutes: number
  }) => {
    const response = await apiClient.post('/pricing/calculate', factors)
    return response.data
  },

  getEstimate: async (taskId: string) => {
    const response = await apiClient.get(`/pricing/estimate/${taskId}`)
    return response.data
  },
}
