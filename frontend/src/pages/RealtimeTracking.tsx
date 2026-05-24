import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'

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
  data: any
}

export default function RealtimeTracking() {
  const { taskId } = useParams()
  const { user } = useAuthStore()
  const [location, setLocation] = useState<LocationData | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [isLive, setIsLive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const socket = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (isLive && (user as any)?.id) {
      connectWebSocket()
    }
    return () => {
      if (socket.current) {
        socket.current.close()
      }
    }
  }, [isLive, user])

  useEffect(() => {
    fetchTrackingData()
    const interval = setInterval(fetchTrackingData, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [taskId])

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/api/v1/tracking/ws/${taskId}`
    socket.current = new WebSocket(wsUrl)

    socket.current.onopen = () => {
      console.log('WebSocket connected')
    }

    socket.current.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data)
      if (data.type === 'location_update') {
        setLocation(data.data)
        addToHistory({
          type: 'location_update',
          timestamp: new Date(),
          data: data.data
        })
      } else if (data.type === 'status_update') {
        setTaskStatus(data.data)
        addToHistory({
          type: 'status_update',
          timestamp: new Date(),
          data: data.data
        })
      }
    }

    socket.current.onerror = (error: Event) => {
      console.error('WebSocket error:', error)
      setError('Lost connection to tracking server')
    }

    socket.current.onclose = () => {
      console.log('WebSocket disconnected')
    }
  }

  const fetchTrackingData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/tracking/${taskId}/location`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setLocation(data.location)
        setTaskStatus(data.status)
      }
    } catch (err) {
      console.error('Failed to fetch tracking data:', err)
    }
  }

  const addToHistory = (entry: HistoryEntry) => {
    setHistory(prev => [entry, ...prev].slice(0, 20)) // Keep last 20 entries
  }

  const handleCheckIn = async () => {
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const response = await fetch(
        `http://localhost:8000/api/v1/tracking/${taskId}/check-in`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy || 0
          })
        }
      )

      if (response.ok) {
        const data = await response.json()
        setTaskStatus(data.status)
        setLocation(data.location)
        addToHistory({
          type: 'check_in',
          timestamp: new Date(),
          data: data.location
        })
      }
    } catch (err) {
      setError('Failed to check in. Please enable location services.')
      console.error(err)
    }
  }

  const handleCheckOut = async () => {
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const response = await fetch(
        `http://localhost:8000/api/v1/tracking/${taskId}/check-out`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          })
        }
      )

      if (response.ok) {
        const data = await response.json()
        setTaskStatus(data.status)
        addToHistory({
          type: 'check_out',
          timestamp: new Date(),
          data: data.location
        })
      }
    } catch (err) {
      setError('Failed to check out. Please enable location services.')
      console.error(err)
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
            {location ? (
              <div className="text-center">
                <p className="text-gray-700 font-semibold">📍 Live Location</p>
                <p className="text-sm text-gray-600 mt-2">
                  Lat: {location.latitude.toFixed(6)}
                </p>
                <p className="text-sm text-gray-600">
                  Lng: {location.longitude.toFixed(6)}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Accuracy: ±{(location.accuracy || 0).toFixed(0)}m
                </p>
              </div>
            ) : (
              <p className="text-gray-600">No location data available</p>
            )}
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
              <p className={`text-lg font-bold mt-1 ${
                taskStatus?.status === 'completed' ? 'text-green-600' :
                taskStatus?.status === 'in_progress' ? 'text-blue-600' :
                'text-yellow-600'
              }`}>
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
            {history.length > 0 ? (
              history.map((entry, index) => (
                <div key={index} className="flex gap-3 text-sm border-b pb-2 last:border-b-0">
                  <div className="text-gray-500 font-mono whitespace-nowrap">
                    {entry.timestamp.toLocaleTimeString()}
                  </div>
                  <div className="flex-1">
                    <span className="font-semibold text-gray-900">
                      {entry.type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-600">No activity yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
