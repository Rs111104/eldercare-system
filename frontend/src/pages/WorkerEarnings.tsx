import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import client from '@/api/client'
import { useStore } from '@/store/useStore'
import type { Payout } from '@/types'

export default function WorkerEarnings() {
  const user = useStore((state) => state.user)
  const [earnings, setEarnings] = useState<{ immediate: number; verification: number; pending: number; total: number } | null>(null)
  const [history, setHistory] = useState<Payout[]>([])

  useEffect(() => {
    async function load() {
      if (!user?.id) return
      try {
        const [{ data: earningsData }, { data: historyData }] = await Promise.all([
          client.get(`/payouts/worker/${user.id}/earnings`),
          client.get<Payout[]>(`/payouts/worker/${user.id}/history`),
        ])
        setEarnings(earningsData)
        setHistory(historyData)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Could not load earnings.')
      }
    }

    void load()
  }, [user?.id])

  return (
    <div className="space-y-6">
      <section className="rounded-[2rem] bg-gradient-to-br from-amber-500 to-rose-500 p-6 text-white shadow-2xl shadow-rose-500/20 sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-amber-100">Payouts</p>
        <h1 className="mt-3 text-3xl font-black tracking-tight">Earnings and split payouts</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-amber-50">Immediate 75% payouts and deferred verification releases are tracked here.</p>
      </section>

      <div className="grid gap-4 sm:grid-cols-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Immediate</p><p className="mt-2 text-3xl font-black text-slate-950">₹{earnings?.immediate.toFixed(0) || '0'}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Verification</p><p className="mt-2 text-3xl font-black text-slate-950">₹{earnings?.verification.toFixed(0) || '0'}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Pending</p><p className="mt-2 text-3xl font-black text-slate-950">₹{earnings?.pending.toFixed(0) || '0'}</p></div>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Total</p><p className="mt-2 text-3xl font-black text-slate-950">₹{earnings?.total.toFixed(0) || '0'}</p></div>
      </div>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">History</p>
        <div className="mt-4 divide-y divide-slate-200">
          {history.length ? history.map((payout) => (
            <div key={payout.id} className="flex items-center justify-between gap-4 py-4 text-sm">
              <div>
                <p className="font-semibold text-slate-950">{payout.split_type}</p>
                <p className="text-slate-500">{payout.status}</p>
              </div>
              <p className="font-black text-slate-950">₹{payout.amount.toFixed(0)}</p>
            </div>
          )) : <div className="py-6 text-sm text-slate-500">No payouts recorded yet.</div>}
        </div>
      </section>
    </div>
  )
}
