import { useState, useEffect } from 'react';

export function DashboardWorker() {
  
  const [profile, setProfile] = useState({
    name: 'Worker Profile',
    rating: 4.8,
    tasks_completed: 0,
    total_earnings: 0,
    service_types: ['medicine', 'help'],
    is_verified: true
  });

  const [availableTasks, setAvailableTasks] = useState<any[]>([]);
  const [activeTasks, setActiveTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'available' | 'active' | 'completed'>('available');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // TODO: Fetch from API
        setProfile({
          name: 'John Doe',
          rating: 4.8,
          tasks_completed: 127,
          total_earnings: 45230,
          service_types: ['medicine', 'help'],
          is_verified: true
        });

        setAvailableTasks([
          {
            task_id: '1',
            title: 'Medicine Delivery',
            description: 'Deliver prescribed medications',
            location: '123 Main St',
            price: 150,
            urgency_level: 3,
            distance: 2.5
          },
          {
            task_id: '2',
            title: 'Household Help',
            description: 'General household assistance',
            location: '456 Oak Ave',
            price: 200,
            urgency_level: 2,
            distance: 3.2
          }
        ]);

        setActiveTasks([]);
      } catch (error) {
        console.error('Failed to fetch tasks', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleAcceptTask = async (taskId: string) => {
    try {
      // TODO: Call API to accept task
      alert(`Task ${taskId} accepted!`);
    } catch (error) {
      console.error('Failed to accept task', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Profile Header */}
        <div className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg text-white p-8 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">{profile.name}</h1>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-lg">★★★★★ {profile.rating}</span>
                {profile.is_verified && (
                  <span className="bg-green-400 text-green-900 px-3 py-1 rounded-full text-sm font-semibold">
                    ✓ Verified
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold">{profile.tasks_completed}</p>
              <p className="text-sm">Tasks Completed</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Total Earnings</p>
            <p className="text-4xl font-bold text-green-500 mt-2">₹{profile.total_earnings}</p>
            <p className="text-xs text-gray-500 mt-2">Lifetime earnings</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Available Tasks</p>
            <p className="text-4xl font-bold text-blue-500 mt-2">{availableTasks.length}</p>
            <p className="text-xs text-gray-500 mt-2">In your area</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 uppercase tracking-wide">Active Today</p>
            <p className="text-4xl font-bold text-purple-500 mt-2">{activeTasks.length}</p>
            <p className="text-xs text-gray-500 mt-2">Ongoing tasks</p>
          </div>
        </div>

        {/* Services Offered */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Services Offered</h2>
          <div className="flex flex-wrap gap-2">
            {profile.service_types.map((type) => (
              <span key={type} className="px-4 py-2 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </span>
            ))}
          </div>
        </div>

        {/* Tasks Section */}
        <div className="bg-white rounded-lg shadow">
          {/* Tabs */}
          <div className="border-b border-gray-200 flex">
            {(['available', 'active', 'completed'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                className={`px-6 py-4 font-semibold border-b-2 transition ${
                  selectedTab === tab
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)} Tasks
                {tab === 'available' && ` (${availableTasks.length})`}
                {tab === 'active' && ` (${activeTasks.length})`}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {selectedTab === 'available' && (
              <div className="space-y-4">
                {availableTasks.length > 0 ? (
                  availableTasks.map((task) => (
                    <div key={task.task_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                          <p className="text-gray-600 text-sm">{task.description}</p>
                        </div>
                        <span className="text-2xl font-bold text-green-500">₹{task.price}</span>
                      </div>

                      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                        <div>
                          <p className="text-gray-600">Location</p>
                          <p className="font-medium">{task.location}</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Distance</p>
                          <p className="font-medium">{task.distance} km</p>
                        </div>
                        <div>
                          <p className="text-gray-600">Urgency</p>
                          <p className="font-medium">⚡ Level {task.urgency_level}/5</p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleAcceptTask(task.task_id)}
                        className="w-full px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 font-semibold"
                      >
                        Accept Task
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No available tasks at the moment</p>
                  </div>
                )}
              </div>
            )}

            {selectedTab === 'active' && (
              <div className="space-y-4">
                {activeTasks.length > 0 ? (
                  activeTasks.map((task) => (
                    <div key={task.task_id} className="border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{task.title}</h3>
                      <p className="text-gray-600 mb-4">{task.description}</p>
                      <button className="px-4 py-2 bg-secondary-500 text-white rounded-lg hover:bg-secondary-600">
                        View Details
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No active tasks</p>
                  </div>
                )}
              </div>
            )}

            {selectedTab === 'completed' && (
              <div className="text-center py-8">
                <p className="text-gray-500">Completed tasks will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardWorker;
