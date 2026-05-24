import { MapPin } from 'lucide-react'

export default function LiveMap({ lat, lng, label }: { lat?: number | null; lng?: number | null; label?: string }) {
  const hasLocation = typeof lat === 'number' && typeof lng === 'number'

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 p-5 text-white shadow-xl">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-sky-300">Live location</p>
          <h3 className="mt-2 text-lg font-semibold">{label || 'Worker tracking'}</h3>
        </div>
        <MapPin className="h-6 w-6 text-sky-300" />
      </div>
      <div className="mt-5 rounded-[2rem] border border-white/10 bg-white/5 p-4">
        <div className="flex h-44 items-center justify-center rounded-[1.5rem] border border-dashed border-white/15 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.22),transparent_48%),linear-gradient(180deg,rgba(15,23,42,1),rgba(2,6,23,1))]">
          {hasLocation ? (
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-sky-400 text-slate-950 shadow-lg shadow-sky-500/30">
                <MapPin className="h-6 w-6" />
              </div>
              <p className="mt-3 text-sm font-medium text-slate-100">{lat?.toFixed(4)}, {lng?.toFixed(4)}</p>
            </div>
          ) : (
            <p className="text-sm text-slate-300">Waiting for the worker to share a live update.</p>
          )}
        </div>
      </div>
    </div>
  )
}
