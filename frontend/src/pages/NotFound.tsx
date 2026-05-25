import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="mx-auto flex min-h-[60vh] max-w-2xl flex-col justify-center gap-5 py-12">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Page not found</p>
      <h1 className="text-3xl font-bold text-slate-950 sm:text-4xl">This page is not available.</h1>
      <p className="text-base leading-7 text-slate-700">
        The link may be old, or you may not have access to this part of ElderCare.
      </p>
      <div className="flex flex-wrap gap-3">
        <Link className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800" to="/">
          Go home
        </Link>
        <Link className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:border-slate-500" to="/login">
          Sign in
        </Link>
      </div>
    </section>
  )
}
