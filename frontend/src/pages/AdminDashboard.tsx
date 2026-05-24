import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'
import WorkerCard from '@/components/WorkerCard'
import type { StatsOverview, Worker } from '@/types'

export default function AdminDashboard() {
  const [stats, setStats] = useState<StatsOverview | null>(null)
  const [pendingWorkers, setPendingWorkers] = useState<Worker[]>([])

  async function loadData() {
    try {
      const [{ data: statsData }, { data: pendingData }] = await Promise.all([
        client.get<StatsOverview>('/admin/stats/overview'),
        client.get<{ workers: Worker[] }>('/onboarding/pending-verifications'),
      ])
      setStats(statsData)
      setPendingWorkers(pendingData.workers || [])
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not load admin dashboard.')
    }
  }

  useEffect(() => {
    void loadData()
  }, [])

  async function approveWorker(workerId: string) {
    try {
      await client.post(`/onboarding/${workerId}/approve`)
      toast.success('Worker approved')
      await loadData()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Could not approve worker.')
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 text-white shadow-2xl shadow-slate-900/20 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-sky-300">Admin</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight">System analytics and approvals</h1>
      </section>

      <div className="grid gap-4 sm:grid-cols-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Customers</p><p className="mt-2 text-3xl font-black">{stats?.total_customers || 0}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Workers</p><p className="mt-2 text-3xl font-black">{stats?.total_workers || 0}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Tasks</p><p className="mt-2 text-3xl font-black">{stats?.total_tasks || 0}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Revenue</p><p className="mt-2 text-3xl font-black">₹{stats?.total_revenue?.toFixed(0) || '0'}</p></div>
      </div>

      <section className="space-y-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Verification queue</p>
          <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950">Approve workers</h2>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {pendingWorkers.length ? pendingWorkers.map((worker) => (
            <div key={worker.id} className="space-y-3">
              <WorkerCard worker={worker} />
              <button onClick={() => void approveWorker(worker.id)} className="w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white">Approve worker</button>
            </div>
          )) : <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">No pending verifications.</div>}
        </div>
      </section>
    </div>
  )
}
