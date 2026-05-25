import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import LiveMap from '@/components/LiveMap'
import type { Task } from '@/types'

export default function TaskTracking() {
  const { taskId } = useParams()
  const [task, setTask] = useState<Task | null>(null)
  const [location, setLocation] = useState<{ lat?: number | null; lng?: number | null } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      if (!taskId) return
      try {
        const [{ data: taskData }, { data: locationData }] = await Promise.all([
          client.get<Task>(`/tasks/${taskId}`),
          client.get(`/tracking/${taskId}/location`),
        ])
        setTask(taskData)
        setLocation(locationData)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Could not load live tracking.')
      } finally {
        setLoading(false)
      }
    }

    void load()
    const timer = window.setInterval(() => void load(), 10000)
    return () => window.clearInterval(timer)
  }, [taskId])

  if (loading) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">Loading live task tracking...</div>
  }

  if (!task) {
    return <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-sm text-rose-700">We could not find that task.</div>
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <section className="space-y-4 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Live task</p>
        <h1 className="text-3xl font-black tracking-tight text-slate-950">{task.title}</h1>
        <p className="text-sm leading-6 text-slate-600">{task.description}</p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl bg-slate-100 p-4"><p className="text-slate-500">Status</p><p className="mt-1 font-semibold text-slate-950">{task.status}</p></div>
          <div className="rounded-2xl bg-slate-100 p-4"><p className="text-slate-500">Price</p><p className="mt-1 font-semibold text-slate-950">₹{task.price.toFixed(0)}</p></div>
          <div className="rounded-2xl bg-slate-100 p-4"><p className="text-slate-500">Service</p><p className="mt-1 font-semibold text-slate-950">{task.service_type}</p></div>
          <div className="rounded-2xl bg-slate-100 p-4"><p className="text-slate-500">Urgency</p><p className="mt-1 font-semibold text-slate-950">{task.urgency}</p></div>
        </div>
      </section>
      <LiveMap lat={location?.lat} lng={location?.lng} label={task.worker_id ? `Worker ${task.worker_id}` : 'Worker en route'} />
    </div>
  )
}
