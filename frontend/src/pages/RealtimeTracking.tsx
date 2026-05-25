import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useStore } from '@/store/useStore'
import client from '@/api/client'

interface LocationData {
  latitude: number
  longitude: number
  timestamp: string
  accuracy?: number
}

interface TaskStatus {
  status?: string
  elapsed_time?: number
  distance?: number
}

interface HistoryEntry {
  type: string
  timestamp: Date
  data: LocationData | TaskStatus | Record<string, unknown>
}

function locationDisplay(location: LocationData | null) {
  if (!location) return <p className="text-gray-600">No location data available</p>
  return (
    <div className="text-center">
      <p className="font-semibold text-gray-700">Live Location</p>
      <p className="mt-2 text-sm text-gray-600">Lat: {location.latitude.toFixed(6)}</p>
      <p className="text-sm text-gray-600">Lng: {location.longitude.toFixed(6)}</p>
      <p className="mt-2 text-xs text-gray-500">Accuracy: ±{(location.accuracy || 0).toFixed(0)}m</p>
    </div>
  )
}

function statusTone(status?: string): string {
  if (status === 'completed') return 'text-green-600'
  if (status === 'in_progress') return 'text-blue-600'
  return 'text-yellow-600'
}

function ActivityHistory({ history }: { history: HistoryEntry[] }) {
  if (history.length === 0) return <p className="text-gray-600">No activity yet</p>
  return (
    <>
      {history.map((entry, index) => (
        <div key={`${entry.type}-${index}`} className="flex gap-3 border-b pb-2 text-sm last:border-b-0">
          <div className="whitespace-nowrap font-mono text-gray-500">{entry.timestamp.toLocaleTimeString()}</div>
          <div className="flex-1">
            <span className="font-semibold text-gray-900">{entry.type.replace('_', ' ').toUpperCase()}</span>
          </div>
        </div>
      ))}
    </>
  )
}

export default function RealtimeTracking() {
  const { taskId } = useParams()
  const user = useStore((state) => state.user)
  const [location, setLocation] = useState<LocationData | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [isLive, setIsLive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const socket = useRef<WebSocket | null>(null)

  const addToHistory = useCallback((entry: HistoryEntry) => {
    setHistory(prev => [entry, ...prev].slice(0, 20))
  }, [])

  const handleSocketMessage = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data) as { type: string; data: LocationData | TaskStatus }
    if (data.type === 'location_update') {
      setLocation(data.data as LocationData)
      addToHistory({ type: 'location_update', timestamp: new Date(), data: data.data })
    }
    if (data.type === 'status_update') {
      setTaskStatus(data.data as TaskStatus)
      addToHistory({ type: 'status_update', timestamp: new Date(), data: data.data })
    }
  }, [addToHistory])

  const connectWebSocket = useCallback(() => {
    const apiBase = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
    const absoluteBase = apiBase.startsWith('http') ? apiBase : `${window.location.origin}${apiBase}`
    const wsUrl = `${absoluteBase.replace(/^http/, 'ws')}/tracking/ws/${taskId}`
    socket.current = new WebSocket(wsUrl)
    socket.current.onmessage = handleSocketMessage

    socket.current.onerror = () => {
      setError('Lost connection to tracking server')
    }
  }, [handleSocketMessage, taskId])

  const fetchTrackingData = useCallback(async () => {
    try {
      const { data } = await client.get(`/tracking/${taskId}/location`)
      setLocation(data ? { latitude: data.lat, longitude: data.lng, timestamp: data.timestamp, accuracy: data.accuracy } : null)
      setTaskStatus(data ? { status: data.event_type } : null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tracking data.')
    }
  }, [taskId])

  useEffect(() => {
    if (isLive && user?.id) connectWebSocket()
    return () => socket.current?.close()
  }, [connectWebSocket, isLive, user?.id])

  useEffect(() => {
    void fetchTrackingData()
    const interval = setInterval(() => void fetchTrackingData(), 5000)
    return () => clearInterval(interval)
  }, [fetchTrackingData])

  const handleCheckIn = async () => {
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const { data } = await client.post(`/tracking/${taskId}/check-in`, null, {
        params: {
          worker_id: user?.id,
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        },
      })
      setLocation({ latitude: data.lat, longitude: data.lng, timestamp: data.timestamp })
      setTaskStatus({ status: data.event_type })
      addToHistory({
        type: 'check_in',
        timestamp: new Date(),
        data
      })
    } catch {
      setError('Failed to check in. Please enable location services.')
    }
  }

  const handleCheckOut = async () => {
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const { data } = await client.post(`/tracking/${taskId}/check-out`, null, {
        params: {
          worker_id: user?.id,
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          report: 'Completed',
        },
      })
      setTaskStatus({ status: data.event_type })
      addToHistory({
        type: 'check_out',
        timestamp: new Date(),
        data
      })
    } catch {
      setError('Failed to check out. Please enable location services.')
    }
  }

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
      {error && (
        <div className="col-span-full bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Map Section */}
      <div className="lg:col-span-2">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Live Location</h2>
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium text-gray-600">
                {isLive ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>

          <div className="bg-gray-200 rounded-lg h-96 flex items-center justify-center mb-4">
            {locationDisplay(location)}
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleCheckIn}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition"
            >
              Check In
            </button>
            <button
              onClick={handleCheckOut}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition"
            >
              Check Out
            </button>
            <button
              onClick={() => setIsLive(!isLive)}
              className={`flex-1 font-bold py-3 px-4 rounded-lg transition ${
                isLive
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-gray-300 hover:bg-gray-400 text-gray-800'
              }`}
            >
              {isLive ? 'Stop Live' : 'Go Live'}
            </button>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Task Status</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">Current Status</p>
              <p className={`text-lg font-bold mt-1 ${statusTone(taskStatus?.status)}`}>
                {taskStatus?.status?.replace('_', ' ').toUpperCase() || 'Unknown'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Elapsed Time</p>
              <p className="text-lg font-bold text-gray-900 mt-1">
                {taskStatus?.elapsed_time || '0:00'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Distance Traveled</p>
              <p className="text-lg font-bold text-gray-900 mt-1">
                {taskStatus?.distance?.toFixed(2) || '0'} km
              </p>
            </div>
          </div>
        </div>

        {/* History */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Activity History</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            <ActivityHistory history={history} />
          </div>
        </div>
      </div>
    </div>
  )
}
