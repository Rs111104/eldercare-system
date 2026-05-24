import type { PricingEstimate } from '@/types'

export default function PriceEstimate({ estimate }: { estimate: PricingEstimate | null }) {
  if (!estimate) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500">
        Price estimate will appear here after you choose a service.
      </div>
    )
  }

  return (
    <div className="rounded-3xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-5 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-[0.24em] text-amber-700">Estimated price</p>
      <div className="mt-2 flex items-end justify-between gap-4">
        <div>
          <p className="text-3xl font-black text-slate-950">₹{estimate.total_price.toFixed(0)}</p>
          <p className="mt-1 text-sm text-slate-600">Base ₹{estimate.base_price.toFixed(0)} + distance + urgency</p>
        </div>
        <div className="rounded-2xl bg-white px-3 py-2 text-right shadow-sm">
          <p className="text-xs font-medium text-slate-500">Urgency</p>
          <p className="text-sm font-semibold text-slate-900">x{estimate.urgency_multiplier.toFixed(2)}</p>
        </div>
      </div>
    </div>
  )
}
