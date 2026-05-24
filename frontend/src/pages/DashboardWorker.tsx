import { useAuthStore } from '@/store/auth'

export default function DashboardWorker() {
  const user = useAuthStore((state) => state.user)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Worker Dashboard</h1>
        <p className="text-gray-600">Welcome, {user?.name}</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-700 mb-2">Rating</h3>
          <p className="text-3xl font-bold text-primary-600">{user?.rating?.toFixed(1) || '5.0'}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-700 mb-2">Tasks Completed</h3>
          <p className="text-3xl font-bold text-primary-600">0</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-700 mb-2">Service Types</h3>
          <p className="text-gray-600">{user?.service_types?.join(', ')}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Available Tasks</h2>
        <p className="text-gray-500">Available tasks will appear here</p>
      </div>
    </div>
  )
}
