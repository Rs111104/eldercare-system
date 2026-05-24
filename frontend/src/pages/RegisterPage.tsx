import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { authService } from '@/services/authService'
import { User, Mail, Phone } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [userType, setUserType] = useState<'customer' | 'worker'>('customer')
  const [formData, setFormData] = useState({
    name: '',
    phoneNumber: '',
    email: '',
    serviceTypes: [] as string[],
  })
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleServiceTypeChange = (service: string) => {
    setFormData((prev) => ({
      ...prev,
      serviceTypes: prev.serviceTypes.includes(service)
        ? prev.serviceTypes.filter((s) => s !== service)
        : [...prev.serviceTypes, service],
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.phoneNumber) {
      toast.error('Please fill in all required fields')
      return
    }

    setIsLoading(true)
    try {
      let response
      if (userType === 'customer') {
        response = await authService.registerCustomer({
          name: formData.name,
          phone_number: formData.phoneNumber,
          email: formData.email,
        })
      } else {
        response = await authService.registerWorker({
          name: formData.name,
          phone_number: formData.phoneNumber,
          email: formData.email,
          service_types: formData.serviceTypes,
          location_lat: 0, // Will be updated
          location_lng: 0,
        })
      }

      login(response.user, response.access_token)
      toast.success('Registration successful!')
      navigate('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-2 text-center">Join ElderCare</h1>
        <p className="text-gray-600 text-center mb-8">Create your account to get started</p>

        {/* User Type Selection */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setUserType('customer')}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
              userType === 'customer'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Need Service
          </button>
          <button
            onClick={() => setUserType('worker')}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
              userType === 'worker'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Offer Service
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <User className="w-4 h-4 inline mr-2" />
              Full Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="John Doe"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Phone className="w-4 h-4 inline mr-2" />
              Phone Number
            </label>
            <input
              type="tel"
              name="phoneNumber"
              value={formData.phoneNumber}
              onChange={handleInputChange}
              placeholder="+91 98765 43210"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Mail className="w-4 h-4 inline mr-2" />
              Email (Optional)
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="john@example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Service Types (for workers) */}
          {userType === 'worker' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Service Types
              </label>
              <div className="space-y-2">
                {['medicine', 'help', 'visit', 'cleaning'].map((service) => (
                  <label key={service} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.serviceTypes.includes(service)}
                      onChange={() => handleServiceTypeChange(service)}
                      className="w-4 h-4 text-primary-600 rounded"
                    />
                    <span className="ml-2 text-gray-700 capitalize">{service}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium mt-6"
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          Already have an account?{' '}
          <a href="/login" className="text-primary-600 hover:underline font-medium">
            Sign In
          </a>
        </p>
      </div>
    </div>
  )
}
