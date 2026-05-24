import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import client from '@/api/client'
import PriceEstimate from '@/components/PriceEstimate'
import { useStore } from '@/store/useStore'
import type { PricingEstimate } from '@/types'

export default function TaskCreate() {
  const navigate = useNavigate()
  const user = useStore((state) => state.user)
  const [title, setTitle] = useState('Medicine Delivery')
  const [description, setDescription] = useState('')
  const [serviceType, setServiceType] = useState('medicine')
  const [urgency, setUrgency] = useState(1.0)
  const [sameDayBundle, setSameDayBundle] = useState(false)
  const [locationLat, setLocationLat] = useState('')
  const [locationLng, setLocationLng] = useState('')
  const [voiceNote, setVoiceNote] = useState<File | null>(null)
  const [estimate, setEstimate] = useState<PricingEstimate | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function updateEstimate(nextServiceType = serviceType, nextUrgency = urgency) {
    try {
      const { data } = await client.post('/pricing/calculate', {
        service_type: nextServiceType,
        distance_km: 0,
        urgency: nextUrgency,
        customer_id: user?.id,
        same_day_bundle: sameDayBundle,
      })
      setEstimate(data)
    } catch {
      setEstimate(null)
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!description.trim()) {
      setError('Please describe what help is needed.')
      return
    }

    if (!user?.id) {
      setError('Sign in first to create a task.')
      return
    }

    setLoading(true)
    try {
      let taskId: string | null = null
      if (voiceNote) {
        const formData = new FormData()
        formData.append('customer_id', user.id)
        formData.append('location_lat', locationLat || '0')
        formData.append('location_lng', locationLng || '0')
        formData.append('audio_file', voiceNote)
        const { data } = await client.post('/tasks/create-from-voice', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        taskId = data.task_id || data.task?.task_id || data.task?.id
      } else {
        const { data } = await client.post('/tasks/create', {
          customer_id: user.id,
          title,
          description,
          task_type: serviceType,
          service_type: serviceType,
          urgency_level: Math.round(1 + ((urgency - 1) / 0.125)),
          urgency,
          location_lat: locationLat ? Number(locationLat) : undefined,
          location_lng: locationLng ? Number(locationLng) : undefined,
          same_day_bundle: sameDayBundle,
        })
        taskId = data.task_id || data.id
      }
      toast.success('Task created')
      navigate(taskId ? `/track/${taskId}` : '/customer')
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Task creation failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <form onSubmit={handleSubmit} className="space-y-5 rounded-[2rem] border border-white/50 bg-white/85 p-6 shadow-2xl shadow-slate-900/5 backdrop-blur-xl sm:p-8">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-rose-500">Create task</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Request care in minutes</h1>
        </div>

        <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Title</span><input value={title} onChange={(event) => setTitle(event.target.value)} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-slate-900" /></label>
        <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Description</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} className="w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-slate-900" placeholder="Describe the care task in a few words" /></label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Service type</span><select value={serviceType} onChange={(event) => { setServiceType(event.target.value); void updateEstimate(event.target.value, urgency) }} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-slate-900"><option value="medicine">Medicine</option><option value="help">Help</option><option value="visit">Visit</option><option value="cleaning">Cleaning</option></select></label>
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Urgency {urgency.toFixed(2)}</span><input value={urgency} onChange={(event) => { const value = Number(event.target.value); setUrgency(value); void updateEstimate(serviceType, value) }} type="range" min="1" max="1.5" step="0.125" className="w-full" /></label>
        </div>

        <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input checked={sameDayBundle} onChange={(event) => { setSameDayBundle(event.target.checked); void updateEstimate(serviceType, urgency) }} type="checkbox" className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-950" />
          <span>
            <span className="block font-semibold text-slate-950">Same-day bundle</span>
            <span className="block text-slate-600">Apply the 15% same-day discount when the job must be handled today.</span>
          </span>
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Latitude</span><input value={locationLat} onChange={(event) => setLocationLat(event.target.value)} type="number" step="any" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-slate-900" /></label>
          <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Longitude</span><input value={locationLng} onChange={(event) => setLocationLng(event.target.value)} type="number" step="any" className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-slate-900" /></label>
        </div>

        <label className="block space-y-2"><span className="text-sm font-semibold text-slate-700">Voice note</span><input type="file" accept="audio/*" onChange={(event) => setVoiceNote(event.target.files?.[0] || null)} className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-full file:border-0 file:bg-slate-950 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white" /></label>

        {error && <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

        <button disabled={loading} className="w-full rounded-2xl bg-slate-950 px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70">{loading ? 'Creating...' : 'Create task'}</button>
      </form>

      <div className="space-y-4">
        <PriceEstimate estimate={estimate} />
        <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-sky-500">Tips</p>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
            <li>Keep the description short and clear.</li>
            <li>Use voice upload when the request is easier to speak than type.</li>
            <li>Coordinates help workers find the location faster.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
