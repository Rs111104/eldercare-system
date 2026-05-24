import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/auth';
import { useTaskStore } from '../store/tasks';

interface NewTask {
  title: string;
  description: string;
  task_type: string;
  mode: 'quick' | 'scheduled';
  urgency_level: number;
  location: string;
}

export function DashboardCustomer() {
  const user = useAuthStore((state) => state.user);
  const tasks = useTaskStore((state) => state.tasks);
  const setTasks = useTaskStore((state) => state.setTasks);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [voiceRecording, setVoiceRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    active_tasks: 0,
    completed_tasks: 0,
    total_spent: 0,
    average_rating: 0
  });

  const [formData, setFormData] = useState<NewTask>({
    title: '',
    description: '',
    task_type: 'medicine',
    mode: 'quick',
    urgency_level: 2,
    location: ''
  });

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        if (user?.user_id) {
          // TODO: Fetch from API
          setTasks([]);
          setStats({
            active_tasks: 2,
            completed_tasks: 15,
            total_spent: 4250,
            average_rating: 4.8
          });
        }
      } catch (error) {
        console.error('Failed to fetch tasks', error);
      }
    };

    fetchTasks();
  }, [user?.user_id, setTasks]);

  const handleCreateTask = async () => {
    setLoading(true);
    try {
      // TODO: Call API to create task
      setShowCreateModal(false);
      setFormData({
        title: '',
        description: '',
        task_type: 'medicine',
        mode: 'quick',
        urgency_level: 2,
        location: ''
      });
    } catch (error) {
      console.error('Failed to create task', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceRecord = async () => {
    setVoiceRecording(!voiceRecording);
    if (voiceRecording) {
      // TODO: Send voice file to API for processing
    }
  };

  const statusColors: Record<string, string> = {
    created: 'bg-yellow-100 text-yellow-800',
    assigned: 'bg-blue-100 text-blue-800',
    accepted: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Tasks</h1>
          <p className="text-gray-600 mt-2">Manage and track your service requests</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Active Tasks</p>
            <p className="text-4xl font-bold text-primary-500 mt-2">{stats.active_tasks}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Completed</p>
            <p className="text-4xl font-bold text-green-500 mt-2">{stats.completed_tasks}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Total Spent</p>
            <p className="text-4xl font-bold text-blue-500 mt-2">₹{stats.total_spent}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Avg Rating</p>
            <p className="text-4xl font-bold text-yellow-400 mt-2">★{stats.average_rating}</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-primary-500 text-white px-6 py-3 rounded-lg hover:bg-primary-600 font-semibold flex items-center justify-center gap-2"
          >
            ➕ New Task
          </button>
          <button
            onClick={handleVoiceRecord}
            className={`px-6 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 ${
              voiceRecording
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'bg-secondary-500 text-white hover:bg-secondary-600'
            }`}
          >
            🎙️ {voiceRecording ? 'Stop Recording' : 'Voice Note'}
          </button>
          <button className="bg-gray-300 text-gray-900 px-6 py-3 rounded-lg hover:bg-gray-400 font-semibold">
            📋 View History
          </button>
        </div>

        {/* Tasks List */}
        <div className="bg-white rounded-lg shadow">
          {tasks && tasks.length > 0 ? (
            <div className="divide-y">
              {tasks.map((task: any) => (
                <div key={task.task_id} className="p-6 hover:bg-gray-50 transition cursor-pointer">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[task.status] || 'bg-gray-100'}`}>
                          {task.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-3">{task.description}</p>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <span>📍 {task.location}</span>
                        <span>⏱️ {task.estimated_time || '30 min'}</span>
                        <span>⚡ Level {task.urgency_level}/5</span>
                      </div>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-2xl font-bold text-primary-500">₹{task.price}</p>
                      <p className="text-xs text-gray-500 mt-1">{new Date(task.created_at).toLocaleDateString()}</p>
                      {task.worker_id && (
                        <p className="text-xs text-green-600 mt-2">✓ Assigned</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <p className="text-gray-500 text-lg mb-4">No tasks yet</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
              >
                Create First Task
              </button>
            </div>
          )}
        </div>

        {/* Create Task Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full p-8 max-h-screen overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Task</h2>

              <div className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Task Title</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="E.g., Medicine Delivery"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Provide details about what you need..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    rows={4}
                  />
                </div>

                {/* Service Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Service Type</label>
                  <select
                    value={formData.task_type}
                    onChange={(e) => setFormData({ ...formData, task_type: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="medicine">Medicine Delivery</option>
                    <option value="help">Household Help</option>
                    <option value="visit">Health Visit</option>
                    <option value="cleaning">Cleaning Services</option>
                  </select>
                </div>

                {/* Mode Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Mode</label>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={() => setFormData({ ...formData, mode: 'quick' })}
                      className={`p-4 border-2 rounded-lg transition ${
                        formData.mode === 'quick'
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <p className="font-semibold">Quick</p>
                      <p className="text-sm text-gray-600">ASAP (30-60 min)</p>
                    </button>
                    <button
                      onClick={() => setFormData({ ...formData, mode: 'scheduled' })}
                      className={`p-4 border-2 rounded-lg transition ${
                        formData.mode === 'scheduled'
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <p className="font-semibold">Scheduled</p>
                      <p className="text-sm text-gray-600">Later (next day+)</p>
                    </button>
                  </div>
                </div>

                {/* Urgency Level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Urgency Level</label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={formData.urgency_level}
                    onChange={(e) => setFormData({ ...formData, urgency_level: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-600 mt-2">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>Critical</span>
                  </div>
                </div>

                {/* Location */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="Full address"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>

                {/* Buttons */}
                <div className="flex gap-4 pt-6">
                  <button
                    onClick={handleCreateTask}
                    disabled={loading || !formData.title}
                    className="flex-1 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-400 font-semibold"
                  >
                    {loading ? 'Creating...' : 'Create Task'}
                  </button>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-6 py-3 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardCustomer;
