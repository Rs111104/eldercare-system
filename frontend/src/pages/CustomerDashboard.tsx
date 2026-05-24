import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import TaskCard from '@/components/TaskCard'
import { useStore } from '@/store/useStore'
import type { Task } from '@/types'

export default function CustomerDashboard() {
  const user = useStore((state) => state.user)
  const tasks = useStore((state) => state.tasks)
  const setTasks = useStore((state) => state.setTasks)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadTasks() {
      if (!user?.id) return
      setLoading(true)
      try {
        const { data } = await client.get<Task[]>(`/tasks/customer/${user.id}`)
        setTasks(data)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Could not load your tasks.')
      } finally {
        setLoading(false)
      }
    }

    void loadTasks()
  }, [setTasks, user?.id])

  const activeTasks = tasks.filter((task) => ['assigned', 'accepted', 'in_progress'].includes(task.status))
  const recentTasks = tasks.slice(0, 6)

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 p-6 text-white shadow-2xl shadow-slate-900/20 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-sky-300">Customer dashboard</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-[1.4fr_0.6fr] sm:items-end">
          <div>
            <h1 className="text-3xl font-black tracking-tight sm:text-4xl">Hello, {user?.name || 'there'}</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-300">Create a task, watch it move, and keep the family updated in one place.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/tasks/new" className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100">Create task</Link>
            <Link to={activeTasks[0] ? `/track/${activeTasks[0].id}` : '/tasks/new'} className="rounded-2xl border border-white/15 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10">Track live</Link>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Total tasks</p><p className="mt-2 text-3xl font-black text-slate-950">{tasks.length}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Active tasks</p><p className="mt-2 text-3xl font-black text-slate-950">{activeTasks.length}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">State</p><p className="mt-2 text-3xl font-black text-slate-950">{loading ? 'Loading' : 'Ready'}</p></div>
      </div>

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] text-rose-500">Task history</p>
            <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950">Recent tasks</h2>
          </div>
          <Link to="/tasks/new" className="text-sm font-semibold text-slate-700 underline decoration-amber-400 decoration-2 underline-offset-4">New request</Link>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {recentTasks.length ? recentTasks.map((task) => <TaskCard key={task.id} task={task} onSelect={() => window.location.assign(`/track/${task.id}`)} />) : <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">No tasks yet. Create the first request to start tracking.</div>}
        </div>
      </section>
    </div>
  )
}
