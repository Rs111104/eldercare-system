import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'
import TaskCard from '@/components/TaskCard'
import { useStore } from '@/store/useStore'
import type { Task, Worker } from '@/types'

export default function WorkerDashboard() {
  const user = useStore((state) => state.user)
  const [profile, setProfile] = useState<Worker | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [loading, setLoading] = useState(true)

  async function loadData() {
    if (!user?.id) return
    setLoading(true)
    try {
      const [{ data: profileData }, { data: taskData }] = await Promise.all([
        client.get<Worker>(`/workers/${user.id}`),
        client.get<Task[]>(`/workers/${user.id}/available-tasks`),
      ])
      setProfile(profileData)
      setTasks(taskData)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not load worker dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [user?.id])

  async function saveLocation() {
    if (!user?.id) return
    try {
      await client.put(`/workers/${user.id}/location`, { latitude: Number(latitude), longitude: Number(longitude) })
      toast.success('Location updated')
      await loadData()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not update location.')
    }
  }

  async function acceptTask(taskId: string) {
    if (!user?.id) return
    try {
      await client.post(`/workers/${user.id}/accept-task/${taskId}`)
      toast.success('Task accepted')
      await loadData()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not accept task.')
    }
  }

  async function rejectTask(taskId: string) {
    if (!user?.id) return
    try {
      await client.post(`/workers/${user.id}/reject-task/${taskId}`)
      toast.success('Task rejected')
      await loadData()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not reject task.')
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-emerald-600 via-slate-900 to-slate-950 p-6 text-white shadow-2xl shadow-slate-900/20 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-emerald-200">Worker dashboard</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight">Welcome, {profile?.name || user?.name || 'worker'}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-200">Keep your location current, review the queue, and manage jobs from a phone-friendly dashboard.</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Available tasks</p><p className="mt-2 text-3xl font-black text-slate-950">{tasks.length}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Verified</p><p className="mt-2 text-3xl font-black text-slate-950">{profile?.is_verified ? 'Yes' : 'Pending'}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Rating</p><p className="mt-2 text-3xl font-black text-slate-950">{profile?.rating?.toFixed(1) || '4.8'}</p></div>
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Latitude</span><input value={latitude} onChange={(event) => setLatitude(event.target.value)} type="number" step="any" className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-900" /></label>
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Longitude</span><input value={longitude} onChange={(event) => setLongitude(event.target.value)} type="number" step="any" className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-slate-900" /></label>
          <button onClick={() => void saveLocation()} className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white">Update location</button>
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Task queue</p>
          <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950">Accept or reject jobs</h2>
        </div>
        {loading ? <div className="rounded-3xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading tasks...</div> : tasks.length ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {tasks.map((task) => (
              <div key={task.id} className="space-y-3">
                <TaskCard task={task} />
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={() => void acceptTask(task.id)} className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white">Accept</button>
                  <button onClick={() => void rejectTask(task.id)} className="rounded-2xl border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-900">Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">No available tasks right now.</div>}
      </section>
    </div>
  )
}
