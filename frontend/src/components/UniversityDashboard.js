import React, { useState, useEffect } from 'react';
import { useAuth } from './Login';

const UniversityDashboard = () => {
  const { user, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [platformStats, setPlatformStats] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchPlatformStats();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/users/me/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
    setLoading(false);
  };

  const fetchPlatformStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/platform/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPlatformStats(data);
      }
    } catch (error) {
      console.error('Error fetching platform stats:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const getRoleBadgeColor = (role) => {
    switch (role?.toLowerCase()) {
      case 'superuser':
        return 'bg-red-100 text-red-800';
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      case 'student':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAccessLevelColor = (level) => {
    switch (level) {
      case 'admin':
        return 'text-red-600';
      case 'control':
        return 'text-orange-600';
      case 'write':
        return 'text-yellow-600';
      case 'read':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                University IoT Research Platform
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {dashboardData?.user_info?.full_name}
                </p>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(dashboardData?.user_info?.role)}`}>
                    {dashboardData?.user_info?.role}
                  </span>
                  {dashboardData?.user_info?.research_area && (
                    <span className="text-xs text-gray-500">
                      {dashboardData.user_info.research_area}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={logout}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 text-white mb-8">
          <h2 className="text-3xl font-bold mb-2">
            Welcome, {dashboardData?.user_info?.full_name}!
          </h2>
          <p className="text-indigo-100">
            {dashboardData?.user_info?.department && `Department: ${dashboardData.user_info.department}`}
          </p>
          {dashboardData?.user_info?.research_area && (
            <p className="text-indigo-100">
              Research Focus: {dashboardData.user_info.research_area}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Available Systems */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Available IoT Systems
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboardData?.available_systems?.map((system, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{system.name}</h4>
                      <span className={`text-sm font-medium ${getAccessLevelColor(system.access_level)}`}>
                        {system.access_level}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{system.description}</p>
                    <div className="flex items-center justify-between">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        system.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {system.status}
                      </span>
                      <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
                        Access System →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activities */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Recent Activities
              </h3>
              <div className="space-y-3">
                {dashboardData?.recent_activities?.slice(0, 5).map((activity, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {activity.action.replace('_', ' ').charAt(0).toUpperCase() + activity.action.slice(1).replace('_', ' ')}
                      </p>
                      <p className="text-xs text-gray-500">
                        {activity.system} • {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                    {activity.details && (
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {activity.details.system_name || activity.details.action || 'Action'}
                      </span>
                    )}
                  </div>
                )) || (
                  <p className="text-gray-500 text-sm">No recent activities</p>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* User Info Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-gray-500">Username</p>
                  <p className="text-sm text-gray-900">{dashboardData?.user_info?.username}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Role</p>
                  <p className="text-sm text-gray-900">{dashboardData?.user_info?.role}</p>
                </div>
                {dashboardData?.user_info?.research_area && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Research Area</p>
                    <p className="text-sm text-gray-900">{dashboardData.user_info.research_area}</p>
                  </div>
                )}
                {dashboardData?.user_info?.department && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Department</p>
                    <p className="text-sm text-gray-900">{dashboardData.user_info.department}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Platform Statistics */}
            {platformStats && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Statistics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Activities</span>
                    <span className="text-sm font-medium text-gray-900">
                      {platformStats.platform_stats?.total_activities || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Users</span>
                    <span className="text-sm font-medium text-gray-900">
                      {platformStats.platform_stats?.unique_users || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Systems</span>
                    <span className="text-sm font-medium text-gray-900">
                      {platformStats.active_systems?.length || 0}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Role-specific Features */}
            {dashboardData?.admin_features && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Admin Features</h3>
                <div className="space-y-2">
                  {Object.entries(dashboardData.admin_features).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        {feature.replace('_', ' ').charAt(0).toUpperCase() + feature.slice(1).replace('_', ' ')}
                      </span>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {dashboardData?.student_features && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Tools</h3>
                <div className="space-y-2">
                  {Object.entries(dashboardData.student_features).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        {feature.replace('_', ' ').charAt(0).toUpperCase() + feature.slice(1).replace('_', ' ')}
                      </span>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        enabled ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {enabled ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UniversityDashboard;
