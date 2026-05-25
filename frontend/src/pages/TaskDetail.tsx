import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { taskService } from '../services/taskService'
import type { Task } from '@/types'

const statusColor: Record<string, string> = {
  created: 'bg-yellow-100 text-yellow-800',
  assigned: 'bg-blue-100 text-blue-800',
  accepted: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

function LoadingState() {
  return <div className="rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading task details...</div>
}

function EmptyState({ onBack }: { onBack: () => void }) {
  return (
    <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
      <h1 className="text-2xl font-bold text-gray-900">Task Not Found</h1>
      <button onClick={onBack} className="mt-4 rounded-lg bg-slate-900 px-6 py-2 text-white" type="button">
        Back to Dashboard
      </button>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold uppercase text-gray-500">{label}</h3>
      <p className="capitalize text-gray-900">{value}</p>
    </div>
  )
}

function TaskSummary({ task }: { task: Task }) {
  const urgency = task.urgency_level || 1
  return (
    <div className="grid grid-cols-2 gap-6 border-b pb-8">
      <DetailRow label="Service Type" value={task.task_type || task.service_type} />
      <DetailRow label="Mode" value={task.mode || 'quick'} />
      <DetailRow label="Urgency" value={`Level ${urgency}/5`} />
      <DetailRow label="Location" value={task.location || 'Shared after confirmation'} />
    </div>
  )
}

function AssignedWorker({ workerId }: { workerId?: string | null }) {
  if (!workerId) return null
  return (
    <div className="border-b pb-8">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">Assigned Worker</h2>
      <div className="rounded-lg bg-gray-50 p-4">
        <p className="font-semibold text-gray-900">Worker #{workerId.slice(0, 8)}</p>
        <p className="text-sm text-gray-600">Rating will appear after more completed jobs.</p>
      </div>
    </div>
  )
}

function CompletedTimeline({ task }: { task: Task }) {
  if (task.status !== 'completed') return null
  return (
    <div className="border-b pb-8">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">Task Timeline</h2>
      <p className="text-sm text-gray-600">Created {new Date(task.created_at).toLocaleString()}</p>
      <p className="mt-2 text-sm text-gray-600">Completed {new Date(task.completed_at || task.created_at).toLocaleString()}</p>
    </div>
  )
}

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchTask() {
      if (!taskId) return
      try {
        const response = await taskService.getTask(taskId)
        setTask(response.data)
      } finally {
        setLoading(false)
      }
    }
    void fetchTask()
  }, [taskId])

  if (loading) return <LoadingState />
  if (!task) return <EmptyState onBack={() => navigate('/dashboard')} />

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <button onClick={() => navigate(-1)} className="font-medium text-slate-700 hover:text-slate-950" type="button">
        Back
      </button>
      <section className="space-y-8 rounded-lg bg-white p-8 shadow-lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{task.title}</h1>
            <span className={`mt-3 inline-block rounded-full px-4 py-2 text-sm font-semibold ${statusColor[task.status] || 'bg-gray-100 text-gray-800'}`}>
              {task.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-slate-900">Rs {task.price.toFixed(0)}</p>
            <p className="mt-1 text-sm text-gray-500">{new Date(task.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        <div className="border-b pb-8">
          <h2 className="mb-3 text-lg font-semibold text-gray-900">Description</h2>
          <p className="leading-relaxed text-gray-700">{task.description}</p>
        </div>
        <TaskSummary task={task} />
        <AssignedWorker workerId={task.worker_id || task.assigned_worker_id} />
        <CompletedTimeline task={task} />
      </section>
    </div>
  )
}

export default TaskDetail
