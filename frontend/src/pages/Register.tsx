import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import { useStore } from '@/store/useStore'
import type { AuthResponse, AuthUser, Role } from '@/types'

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

export default function Register() {
  const navigate = useNavigate()
  const login = useStore((state) => state.login)
  const [role, setRole] = useState<Role>('customer')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [serviceType, setServiceType] = useState('help')
  const [address, setAddress] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!phone.trim() || !password.trim()) {
      setError('Phone number and password are required.')
      return
    }

    setLoading(true)
    try {
      const payload = {
        phone_number: phone.trim(),
        password,
        name: name.trim() || (role === 'worker' ? 'Worker' : 'Customer'),
        service_type: role === 'worker' ? serviceType : undefined,
        service_types: role === 'worker' ? [serviceType] : [],
        address: role === 'customer' ? address.trim() : '',
      }
      const endpoint = role === 'worker' ? '/auth/register/worker' : '/auth/register/customer'
      const { data } = await client.post<AuthResponse>(endpoint, payload)
      login(normalizeUser(data), data.access_token)
      toast.success('Account created')
      navigate(role === 'worker' ? '/worker' : '/customer')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-2xl items-center px-4 py-10">
      <form onSubmit={handleSubmit} className="w-full space-y-6 rounded-[2rem] border border-white/50 bg-white/80 p-6 shadow-2xl shadow-slate-900/5 backdrop-blur-xl sm:p-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Get started</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Create account</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">Choose the role you need and we’ll wire your dashboard to the right workflow.</p>
        </div>

        <div className="grid grid-cols-3 gap-2 rounded-2xl bg-slate-100 p-2">
          {(['customer', 'worker', 'admin'] as Role[]).map((value) => (
            <button key={value} type="button" onClick={() => setRole(value)} className={["rounded-2xl px-3 py-2 text-sm font-semibold capitalize transition", role === value ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500 hover:text-slate-900'].join(' ')}>
              {value}
            </button>
          ))}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">Name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} type="text" placeholder="Full name" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">Phone number</span>
            <input value={phone} onChange={(event) => setPhone(event.target.value)} type="tel" placeholder="+919876543210" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-semibold text-slate-700">Password</span>
            <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="Create a strong password" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
          </label>
          {role === 'worker' ? (
            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">Service type</span>
              <select value={serviceType} onChange={(event) => setServiceType(event.target.value)} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900">
                <option value="medicine">Medicine</option>
                <option value="help">Help</option>
                <option value="visit">Visit</option>
                <option value="cleaning">Cleaning</option>
              </select>
            </label>
          ) : (
            <label className="block space-y-2">
              <span className="text-sm font-semibold text-slate-700">Address</span>
              <input value={address} onChange={(event) => setAddress(event.target.value)} type="text" placeholder="Home address" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none transition focus:border-slate-900" />
            </label>
          )}
        </div>

        {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

        <button disabled={loading} className="w-full rounded-2xl bg-slate-950 px-4 py-3.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70">
          {loading ? 'Creating account...' : `Create ${role} account`}
        </button>

        <p className="text-center text-sm text-slate-600">
          Already have an account? <Link to="/login" className="font-semibold text-slate-950 underline decoration-amber-400 decoration-2 underline-offset-4">Sign in</Link>
        </p>
      </form>
    </div>
  )
}
