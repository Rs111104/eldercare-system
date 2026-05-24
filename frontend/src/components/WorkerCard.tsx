import { Star, MapPinned, BadgeCheck } from 'lucide-react'
import type { Worker } from '@/types'

export default function WorkerCard({ worker, onSelect }: { worker: Worker; onSelect?: (worker: Worker) => void }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-950">{worker.name}</h3>
            {worker.is_verified && <BadgeCheck className="h-5 w-5 text-emerald-600" />}
          </div>
          <p className="mt-1 text-sm text-slate-600">{worker.service_type}</p>
        </div>
        <div className="rounded-2xl bg-emerald-50 px-3 py-2 text-right">
          <p className="text-xs font-medium text-emerald-700">Rating</p>
          <p className="text-lg font-black text-emerald-900">{worker.rating.toFixed(1)}</p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-3 text-sm text-slate-600">
        <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2"><Star className="h-4 w-4" />{worker.rating.toFixed(1)}</span>
        <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2"><MapPinned className="h-4 w-4" />{worker.distance_km ?? 0} km</span>
      </div>
      {onSelect && (
        <button onClick={() => onSelect(worker)} className="mt-5 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-50">
          Select worker
        </button>
      )}
    </article>
  )
}
