import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { LogOut, Menu, ShieldCheck } from 'lucide-react'
import { useStore } from '@/store/useStore'

export default function Navbar() {
  const user = useStore((state) => state.user)
  const logout = useStore((state) => state.logout)
  const [open, setOpen] = useState(false)

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-4 py-2 text-sm font-semibold transition ${isActive ? 'bg-slate-950 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'}`

  return (
    <header className="sticky top-0 z-40 border-b border-white/30 bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-rose-500 text-white shadow-lg shadow-rose-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-black tracking-tight text-slate-950">ElderCare</p>
            <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-500">Care network</p>
          </div>
        </Link>

        <button className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white p-3 text-slate-700 shadow-sm sm:hidden" onClick={() => setOpen((value) => !value)}>
          <Menu className="h-5 w-5" />
        </button>

        <nav className="hidden items-center gap-2 sm:flex">
          <NavLink to="/" className={navClass}>Home</NavLink>
          {user?.role === 'customer' && <NavLink to="/customer" className={navClass}>Customer</NavLink>}
          {user?.role === 'worker' && <NavLink to="/worker" className={navClass}>Worker</NavLink>}
          {user?.role === 'admin' && <NavLink to="/admin" className={navClass}>Admin</NavLink>}
          {!user ? (
            <>
              <NavLink to="/login" className={navClass}>Login</NavLink>
              <NavLink to="/register" className={navClass}>Register</NavLink>
            </>
          ) : (
            <button onClick={logout} className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800">
              <LogOut className="h-4 w-4" />Logout
            </button>
          )}
        </nav>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-white px-4 py-4 sm:hidden">
          <div className="flex flex-col gap-2">
            <NavLink to="/" className={navClass} onClick={() => setOpen(false)}>Home</NavLink>
            {!user ? (
              <>
                <NavLink to="/login" className={navClass} onClick={() => setOpen(false)}>Login</NavLink>
                <NavLink to="/register" className={navClass} onClick={() => setOpen(false)}>Register</NavLink>
              </>
            ) : (
              <button onClick={() => { logout(); setOpen(false) }} className="rounded-full bg-slate-950 px-4 py-3 text-left text-sm font-semibold text-white">Logout</button>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
