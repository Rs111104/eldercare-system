import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { useTaskStore } from '@/store/tasks'
import { taskService } from '@/services/taskService'
import { Task } from '@/store/tasks'
import toast from 'react-hot-toast'

export default function DashboardCustomer() {
  const user = useAuthStore((state) => state.user)
  const tasks = useTaskStore((state) => state.tasks)
  const setTasks = useTaskStore((state) => state.setTasks)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (user?.user_id) {
      loadCustomerTasks()
    }
  }, [user])

  const loadCustomerTasks = async () => {
    try {
      const data = await taskService.getCustomerTasks(user?.user_id || '')
      setTasks(data)
    } catch (error: any) {
      toast.error('Failed to load tasks')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Welcome, {user?.name}</h1>
        <p className="text-gray-600">Manage your ElderCare service requests</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Your Tasks</h2>
        {tasks.length === 0 ? (
          <p className="text-gray-500">No tasks yet. Create one to get started!</p>
        ) : (
          <div className="space-y-4">
            {tasks.map((task: Task) => (
              <div key={task.task_id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold">{task.title}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    task.status === 'completed' ? 'bg-green-100 text-green-800' :
                    task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                    task.status === 'accepted' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {task.status}
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-2">{task.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">₹{task.estimated_price}</span>
                  {task.assigned_worker_id && (
                    <span className="text-sm text-primary-600">Worker assigned</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
