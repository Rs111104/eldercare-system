import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { taskService } from '../services/taskService';

export function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showRatingForm, setShowRatingForm] = useState(false);
  const [rating, setRating] = useState(5);
  const [review, setReview] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchTask = async () => {
      try {
        if (taskId) {
          const response = await taskService.getTask(taskId);
          setTask(response.data);
          
          // Fetch worker details if assigned
          if (response.data.worker_id) {
            // TODO: Fetch worker details
          }
        }
      } catch (error) {
        console.error('Failed to fetch task', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTask();
  }, [taskId]);

  const handleRatingSubmit = async () => {
    setSubmitting(true);
    try {
      // TODO: Submit rating and review
      setShowRatingForm(false);
      setRating(5);
      setReview('');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Task Not Found</h1>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const statusColor: Record<string, string> = {
    created: 'bg-yellow-100 text-yellow-800',
    assigned: 'bg-blue-100 text-blue-800',
    accepted: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-primary-500 hover:text-primary-700 font-medium"
        >
          ← Back
        </button>

        {/* Task Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{task.title}</h1>
              <span className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${statusColor[task.status] || 'bg-gray-100 text-gray-800'}`}>
                {task.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-primary-500">₹{task.price}</p>
              <p className="text-sm text-gray-500 mt-1">{new Date(task.created_at).toLocaleDateString()}</p>
            </div>
          </div>

          {/* Description */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Description</h2>
            <p className="text-gray-700 leading-relaxed">{task.description}</p>
          </div>

          {/* Task Details Grid */}
          <div className="grid grid-cols-2 gap-6 mb-8 pb-8 border-b">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Service Type</h3>
              <p className="text-gray-900 capitalize">{task.task_type}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Mode</h3>
              <p className="text-gray-900 capitalize">{task.mode}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Urgency</h3>
              <p className="text-gray-900">{'⚡'.repeat(task.urgency_level)} Level {task.urgency_level}/5</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Location</h3>
              <p className="text-gray-900">{task.location}</p>
            </div>
          </div>

          {/* Worker Info */}
          {task.worker_id && (
            <div className="mb-8 pb-8 border-b">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Assigned Worker</h2>
              <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-semibold text-gray-900">Worker #{task.worker_id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-600">★★★★★ 4.8 rating</p>
                </div>
                <button className="ml-auto px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600">
                  Contact
                </button>
              </div>
            </div>
          )}

          {/* Timeline */}
          {task.status === 'completed' && (
            <div className="mb-8 pb-8 border-b">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Task Timeline</h2>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <div className="w-4 h-4 rounded-full bg-green-500 mt-1 flex-shrink-0"></div>
                  <div>
                    <p className="font-semibold text-gray-900">Task Created</p>
                    <p className="text-sm text-gray-600">{new Date(task.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-4 h-4 rounded-full bg-green-500 mt-1 flex-shrink-0"></div>
                  <div>
                    <p className="font-semibold text-gray-900">Worker Assigned</p>
                    <p className="text-sm text-gray-600">In progress...</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-4 h-4 rounded-full bg-green-500 mt-1 flex-shrink-0"></div>
                  <div>
                    <p className="font-semibold text-gray-900">Task Completed</p>
                    <p className="text-sm text-gray-600">{new Date(task.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Rating Form */}
          {task.status === 'completed' && !showRatingForm && (
            <button
              onClick={() => setShowRatingForm(true)}
              className="w-full px-6 py-3 bg-secondary-500 text-white rounded-lg hover:bg-secondary-600 font-semibold"
            >
              Rate This Service
            </button>
          )}

          {showRatingForm && (
            <div className="p-6 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Your Experience</h3>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">Rating</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className={`text-3xl transition ${
                        star <= rating ? 'text-yellow-400' : 'text-gray-300'
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Review (Optional)</label>
                <textarea
                  value={review}
                  onChange={(e) => setReview(e.target.value)}
                  placeholder="Share your experience with this service..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={4}
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleRatingSubmit}
                  disabled={submitting}
                  className="flex-1 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-400 font-semibold"
                >
                  {submitting ? 'Submitting...' : 'Submit Review'}
                </button>
                <button
                  onClick={() => setShowRatingForm(false)}
                  className="flex-1 px-6 py-3 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-semibold"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TaskDetail;
