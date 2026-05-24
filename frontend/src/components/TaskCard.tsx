import { Clock3, MapPin, Star } from 'lucide-react'
import type { Task } from '@/types'

export default function TaskCard({ task, onSelect }: { task: Task; onSelect?: (task: Task) => void }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-rose-500">{task.status}</p>
          <h3 className="mt-1 text-lg font-semibold text-slate-950">{task.title}</h3>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{task.description}</p>
        </div>
        <div className="rounded-2xl bg-amber-50 px-3 py-2 text-right">
          <p className="text-xs font-medium text-amber-700">Price</p>
          <p className="text-lg font-black text-amber-900">₹{task.price.toFixed(0)}</p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-3 text-sm text-slate-600">
        <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2"><Clock3 className="h-4 w-4" />Urgency {task.urgency}</span>
        <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2"><MapPin className="h-4 w-4" />{task.service_type}</span>
        {typeof task.matched_workers?.length === 'number' && (
          <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2"><Star className="h-4 w-4" />{task.matched_workers.length} workers</span>
        )}
      </div>
      {onSelect && (
        <button onClick={() => onSelect(task)} className="mt-5 w-full rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
          View task
        </button>
      )}
    </article>
  )
}
