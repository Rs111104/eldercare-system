import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/auth';

export function WorkerProfile() {
  const { workerId } = useParams<{ workerId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    phone: '',
    service_types: [] as string[],
    bio: '',
    profile_picture_url: '',
    is_verified: false
  });

  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    tasks_completed: 0,
    average_rating: 0,
    total_earnings: 0,
    response_time: '0 min'
  });

  const serviceTypeOptions = [
    { id: 'medicine', label: 'Medicine Delivery' },
    { id: 'help', label: 'Household Help' },
    { id: 'visit', label: 'Health Visit' },
    { id: 'cleaning', label: 'Cleaning Services' }
  ];

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        // TODO: Fetch profile from API
        setProfile({
          name: 'John Doe',
          email: 'john@example.com',
          phone: '+91 98765 43210',
          service_types: ['medicine', 'help'],
          bio: 'Experienced healthcare professional with 5 years of experience',
          profile_picture_url: '',
          is_verified: true
        });

        setStats({
          tasks_completed: 127,
          average_rating: 4.8,
          total_earnings: 45230,
          response_time: '2 min'
        });
      } catch (error) {
        console.error('Failed to fetch profile', error);
      }
    };

    fetchProfile();
  }, [workerId]);

  const handleServiceTypeChange = (serviceId: string) => {
    setProfile(prev => ({
      ...prev,
      service_types: prev.service_types.includes(serviceId)
        ? prev.service_types.filter(s => s !== serviceId)
        : [...prev.service_types, serviceId]
    }));
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      // TODO: Save profile to API
      setEditing(false);
    } catch (error) {
      console.error('Failed to save profile', error);
    } finally {
      setLoading(false);
    }
  };

  const isOwnProfile = user?.user_id === workerId;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-primary-500 hover:text-primary-700 font-medium"
        >
          ← Back
        </button>

        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div className="flex gap-6">
              <div className="w-24 h-24 bg-gradient-to-br from-primary-400 to-secondary-400 rounded-full flex items-center justify-center text-white text-3xl">
                👤
              </div>
              <div>
                {!editing ? (
                  <>
                    <h1 className="text-3xl font-bold text-gray-900">{profile.name}</h1>
                    <p className="text-gray-600 mt-1">{profile.email}</p>
                    <p className="text-gray-600">{profile.phone}</p>
                    {profile.is_verified && (
                      <span className="inline-block mt-2 px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full font-semibold">
                        ✓ Verified Worker
                      </span>
                    )}
                  </>
                ) : (
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={profile.name}
                      onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                      placeholder="Full Name"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                      placeholder="Email"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                )}
              </div>
            </div>

            {isOwnProfile && (
              <button
                onClick={() => setEditing(!editing)}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 font-semibold"
              >
                {editing ? 'Cancel' : 'Edit Profile'}
              </button>
            )}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-4 mb-8 pb-8 border-b">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary-500">{stats.tasks_completed}</p>
              <p className="text-sm text-gray-600 mt-1">Tasks Completed</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-400">★{stats.average_rating}</p>
              <p className="text-sm text-gray-600 mt-1">Average Rating</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-500">₹{stats.total_earnings}</p>
              <p className="text-sm text-gray-600 mt-1">Total Earnings</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-500">{stats.response_time}</p>
              <p className="text-sm text-gray-600 mt-1">Avg Response Time</p>
            </div>
          </div>

          {/* Bio */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">About</h2>
            {!editing ? (
              <p className="text-gray-700">{profile.bio || 'No bio added yet'}</p>
            ) : (
              <textarea
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                placeholder="Tell customers about yourself..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={4}
              />
            )}
          </div>

          {/* Service Types */}
          <div className="mb-8 pb-8 border-b">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Services Offered</h2>
            {!editing ? (
              <div className="flex flex-wrap gap-2">
                {profile.service_types.map((type) => {
                  const option = serviceTypeOptions.find(s => s.id === type);
                  return (
                    <span key={type} className="px-4 py-2 bg-primary-100 text-primary-800 rounded-full text-sm font-medium">
                      {option?.label}
                    </span>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-3">
                {serviceTypeOptions.map((option) => (
                  <label key={option.id} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={profile.service_types.includes(option.id)}
                      onChange={() => handleServiceTypeChange(option.id)}
                      className="w-5 h-5 text-primary-500 rounded focus:outline-none"
                    />
                    <span className="text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Recent Reviews */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Reviews</h2>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-semibold text-gray-900">Customer {i}</p>
                    <span className="text-yellow-400">★★★★★</span>
                  </div>
                  <p className="text-gray-600">
                    Great service! Very professional and timely. Would recommend to others.
                  </p>
                  <p className="text-xs text-gray-500 mt-2">2 days ago</p>
                </div>
              ))}
            </div>
          </div>

          {/* Save Changes */}
          {editing && (
            <div className="flex gap-3">
              <button
                onClick={handleSaveProfile}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-400 font-semibold"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="flex-1 px-6 py-3 bg-gray-300 text-gray-900 rounded-lg hover:bg-gray-400 font-semibold"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default WorkerProfile;
