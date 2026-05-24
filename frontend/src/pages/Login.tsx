import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import { useStore } from '@/store/useStore'
import type { AuthResponse, AuthUser } from '@/types'

function normalizeUser(response: AuthResponse): AuthUser {
  return {
    id: response.user_id,
    phone: response.user.phone || response.user.phone_number || '',
    name: response.user.name,
    role: response.user_type,
    service_type: response.user.service_type,
    rating: response.user.rating,
    is_verified: response.user.is_verified,
  }
}

export default function Login() {
  const navigate = useNavigate()
  const login = useStore((state) => state.login)
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!phone.trim() || !password.trim()) {
      setError('Enter your phone number and password.')
      return
    }

    setLoading(true)
    try {
      const { data } = await client.post<AuthResponse>('/auth/login', { phone_number: phone.trim(), password })
      login(normalizeUser(data), data.access_token)
      toast.success('Signed in successfully')
      navigate(data.user_type === 'worker' ? '/worker' : data.user_type === 'admin' ? '/admin' : '/customer')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Sign in failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md items-center px-4 py-10">
      <form onSubmit={handleSubmit} className="w-full space-y-6 rounded-[2rem] border border-white/50 bg-white/80 p-6 shadow-2xl shadow-slate-900/5 backdrop-blur-xl sm:p-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Welcome back</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Sign in</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">Use the phone number tied to your customer or worker account.</p>
        </div>

        <label className="block space-y-2">
          <span className="text-sm font-semibold text-slate-700">Phone number</span>
          <input value={phone} onChange={(event) => setPhone(event.target.value)} type="tel" placeholder="+919876543210" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-semibold text-slate-700">Password</span>
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="••••••••" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
        </label>

        {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

        <button disabled={loading} className="w-full rounded-2xl bg-slate-950 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70">
          {loading ? 'Signing in...' : 'Sign in'}
        </button>

        <p className="text-center text-sm text-slate-600">
          Need an account? <Link to="/register" className="font-semibold text-slate-950 underline decoration-amber-400 decoration-2 underline-offset-4">Create one</Link>
        </p>
      </form>
    </div>
  )
}
