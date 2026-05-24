import { Link } from 'react-router-dom'
import { ArrowRight, HeartPulse, MessageSquare, MapPinned } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="space-y-10">
      <section className="overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-slate-950 via-slate-900 to-rose-950 p-6 text-white shadow-2xl shadow-slate-900/20 sm:p-10 lg:p-14">
        <div className="max-w-3xl space-y-6">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-amber-300">Eldercare network</p>
          <h1 className="text-4xl font-black tracking-tight sm:text-6xl">Verified help for elderly families, delivered on time.</h1>
          <p className="max-w-2xl text-base leading-7 text-slate-200 sm:text-lg">A mobile-first platform connecting customers with approved care workers, live tracking, split payouts, and WhatsApp-first task creation.</p>
          <div className="flex flex-wrap gap-3">
            <Link to="/register" className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-white/10 transition hover:bg-slate-100">Get started <ArrowRight className="h-4 w-4" /></Link>
            <Link to="/login" className="inline-flex items-center gap-2 rounded-full border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10">Sign in</Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <HeartPulse className="h-10 w-10 text-rose-500" />
          <h3 className="mt-4 text-xl font-bold text-slate-950">Care-first design</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">Simple flows, larger touch targets, and fast access to live help.</p>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <MessageSquare className="h-10 w-10 text-amber-500" />
          <h3 className="mt-4 text-xl font-bold text-slate-950">WhatsApp-driven tasks</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">Create requests with text or voice and move straight into dispatch.</p>
        </div>
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <MapPinned className="h-10 w-10 text-sky-500" />
          <h3 className="mt-4 text-xl font-bold text-slate-950">Live worker tracking</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">Monitor location updates and task status from any phone screen.</p>
        </div>
      </section>

      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <h2 className="text-2xl font-black tracking-tight text-slate-950">How it works</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {[
            ['1', 'Create account', 'Choose customer or worker to start the right flow.'],
            ['2', 'Raise a task', 'Use a form or voice note to describe the need.'],
            ['3', 'Match and track', 'Verified workers accept, move, and report live.'],
            ['4', 'Complete and pay', 'Payouts split 75/25 with verification release.'],
          ].map(([step, title, description]) => (
            <div key={step} className="rounded-3xl bg-slate-50 p-5">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white">{step}</div>
              <h3 className="mt-4 text-lg font-bold text-slate-950">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
