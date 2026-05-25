import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import ErrorBoundary from '@/components/ErrorBoundary'
import Navbar from '@/components/Navbar'
import { useStore } from '@/store/useStore'
import LandingPage from '@/pages/LandingPage'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import CustomerDashboard from '@/pages/CustomerDashboard'
import TaskCreate from '@/pages/TaskCreate'
import TaskTracking from '@/pages/TaskTracking'
import WorkerDashboard from '@/pages/WorkerDashboard'
import WorkerEarnings from '@/pages/WorkerEarnings'
import NotFound from '@/pages/NotFound'

function RoleRedirect() {
  const user = useStore((state) => state.user)
  if (!user) return <LandingPage />
  if (user.role === 'worker') return <Navigate to="/worker" replace />
  return <Navigate to="/customer" replace />
}

function RequireRole({ role, children }: { role: 'customer' | 'worker' | 'admin'; children: React.ReactNode }) {
  const user = useStore((state) => state.user)
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(251,191,36,0.16),transparent_32%),linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)] text-slate-900">
        <Navbar />
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<RoleRedirect />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/customer" element={<RequireRole role="customer"><CustomerDashboard /></RequireRole>} />
              <Route path="/tasks/new" element={<RequireRole role="customer"><TaskCreate /></RequireRole>} />
              <Route path="/track/:taskId" element={<RequireRole role="customer"><TaskTracking /></RequireRole>} />
              <Route path="/worker" element={<RequireRole role="worker"><WorkerDashboard /></RequireRole>} />
              <Route path="/worker/earnings" element={<RequireRole role="worker"><WorkerEarnings /></RequireRole>} />
              <Route path="/dashboard" element={<RoleRedirect />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </ErrorBoundary>
        </main>
        <Toaster position="top-right" />
      </div>
    </BrowserRouter>
  )
}
