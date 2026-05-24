import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'

export default function WorkerOnboarding() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    service_types: [] as string[],
    experience_years: 0,
    hourly_rate: 0,
    bio: '',
    languages: [] as string[],
    availability: 'full_time',
    certifications: [] as string[]
  })

  const serviceTypes = [
    { id: 'medicine', label: 'Medicine Delivery' },
    { id: 'help', label: 'Personal Help' },
    { id: 'visit', label: 'Health Visit' },
    { id: 'cleaning', label: 'Cleaning' }
  ]

  const languages = ['Hindi', 'English', 'Marathi', 'Tamil', 'Bengali']

  const handleServiceTypeChange = (serviceType: string) => {
    setFormData(prev => ({
      ...prev,
      service_types: prev.service_types.includes(serviceType)
        ? prev.service_types.filter(s => s !== serviceType)
        : [...prev.service_types, serviceType]
    }))
  }

  const handleLanguageChange = (lang: string) => {
    setFormData(prev => ({
      ...prev,
      languages: prev.languages.includes(lang)
        ? prev.languages.filter(l => l !== lang)
        : [...prev.languages, lang]
    }))
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: ['experience_years', 'hourly_rate'].includes(name) ? parseFloat(value) : value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (step < 3) {
      setStep(step + 1)
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      // Save worker onboarding data
      const response = await fetch('http://localhost:8000/api/v1/workers/onboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          worker_id: (user as any)?.id,
          ...formData
        })
      })

      if (!response.ok) {
        throw new Error('Failed to complete onboarding')
      }

      navigate('/dashboard')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Worker Onboarding</h1>
          <p className="text-gray-600 text-lg mb-8">Step {step} of 3</p>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {step === 1 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Basic Information</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="10-digit phone number"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bio
                  </label>
                  <textarea
                    name="bio"
                    value={formData.bio}
                    onChange={handleInputChange}
                    rows={4}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Tell customers about yourself"
                  />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Services & Skills</h2>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-4">
                    Services You Can Provide (Select at least one)
                  </label>
                  <div className="space-y-3">
                    {serviceTypes.map(service => (
                      <label key={service.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.service_types.includes(service.id)}
                          onChange={() => handleServiceTypeChange(service.id)}
                          className="h-4 w-4 text-blue-600 rounded"
                        />
                        <span className="ml-3 text-gray-700">{service.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Years of Experience
                    </label>
                    <input
                      type="number"
                      name="experience_years"
                      value={formData.experience_years}
                      onChange={handleInputChange}
                      min="0"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Preferred Hourly Rate (₹)
                    </label>
                    <input
                      type="number"
                      name="hourly_rate"
                      value={formData.hourly_rate}
                      onChange={handleInputChange}
                      min="0"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-4">
                    Languages You Speak
                  </label>
                  <div className="space-y-3">
                    {languages.map(lang => (
                      <label key={lang} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.languages.includes(lang)}
                          onChange={() => handleLanguageChange(lang)}
                          className="h-4 w-4 text-blue-600 rounded"
                        />
                        <span className="ml-3 text-gray-700">{lang}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Availability & Documents</h2>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Availability
                  </label>
                  <select
                    name="availability"
                    value={formData.availability}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="full_time">Full Time</option>
                    <option value="part_time">Part Time</option>
                    <option value="flexible">Flexible</option>
                    <option value="weekends_only">Weekends Only</option>
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-2">Verification Requirements</h3>
                  <ul className="text-blue-700 space-y-2 text-sm">
                    <li>✓ Valid ID proof will be verified</li>
                    <li>✓ Phone number will be confirmed</li>
                    <li>✓ Background check will be conducted</li>
                    <li>✓ Services will be verified before going live</li>
                  </ul>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-2">You're Almost Done!</h3>
                  <p className="text-green-700 text-sm">
                    Complete your profile and start accepting tasks. You'll earn ₹{formData.hourly_rate ? (formData.hourly_rate * 0.75).toFixed(2) : '0'} per hour.
                  </p>
                </div>
              </div>
            )}

            <div className="flex gap-4 mt-8">
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition"
                >
                  Previous
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className={`flex-1 px-6 py-3 font-semibold rounded-lg text-white transition ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {loading ? 'Saving...' : step === 3 ? 'Complete Onboarding' : 'Next Step'}
              </button>
            </div>
          </form>

          <div className="mt-6 flex gap-2">
            {[1, 2, 3].map(i => (
              <div
                key={i}
                className={`h-2 flex-1 rounded-full ${
                  i <= step ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
