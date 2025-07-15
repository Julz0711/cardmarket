import React, { useState, useEffect } from "react";
import { api } from "../../api/client";

// Material Icons
import PersonIcon from "@mui/icons-material/Person";
import EmailIcon from "@mui/icons-material/Email";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import LoginIcon from "@mui/icons-material/Login";

interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getAllUsers();
      setUsers(response.users);
    } catch (error) {
      console.error("Failed to load users:", error);
      setError(error instanceof Error ? error.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return "Invalid date";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse mx-auto mb-4" />
        <p className="text-muted">Loading users...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="text-center py-8">
            <div className="text-red-500 mb-4">
              <PersonIcon fontSize="large" />
            </div>
            <h3 className="text-lg font-medium text-primary mb-2">
              Error Loading Users
            </h3>
            <p className="text-muted mb-4">{error}</p>
            <button onClick={loadUsers} className="primary-btn">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-primary flex items-center">
              <PersonIcon className="mr-2" />
              User Management
            </h2>
            <button onClick={loadUsers} className="primary-btn">
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Users Summary */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-primary">Summary</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-3 gap-4">
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Total Users
              </div>
              <div className="text-2xl font-bold text-primary">
                {users.length}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Active Users
              </div>
              <div className="text-2xl font-bold text-primary">
                {users.filter((user) => user.last_login).length}
              </div>
            </div>
            <div className="stats-card">
              <div className="text-sm font-medium text-secondary">
                Recent Signups
              </div>
              <div className="text-2xl font-bold text-primary">
                {
                  users.filter((user) => {
                    const createdDate = new Date(user.created_at);
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return createdDate > weekAgo;
                  }).length
                }
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-primary">
            All Users ({users.length})
          </h3>
        </div>
        <div className="card-body">
          {users.length === 0 ? (
            <div className="px-6 py-8 text-center text-secondary">
              <PersonIcon fontSize="large" className="mb-4 opacity-50" />
              <p>No users found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-600">
                <thead className="bg-tertiary">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      <div className="flex items-center">
                        <PersonIcon fontSize="small" className="mr-1" />
                        User ID
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      <div className="flex items-center">
                        <PersonIcon fontSize="small" className="mr-1" />
                        Username
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      <div className="flex items-center">
                        <EmailIcon fontSize="small" className="mr-1" />
                        Email
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      <div className="flex items-center">
                        <CalendarTodayIcon fontSize="small" className="mr-1" />
                        Created At
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      <div className="flex items-center">
                        <LoginIcon fontSize="small" className="mr-1" />
                        Last Login
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-secondary divide-y divide-gray-600">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-tertiary">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-primary">
                          {user.id.slice(-8)} {/* Show last 8 chars of ID */}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-primary">
                          {user.username}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-secondary">
                          {user.email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-secondary">
                          {formatDate(user.created_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-secondary">
                          {user.last_login
                            ? formatDate(user.last_login)
                            : "Never"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.last_login
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {user.last_login ? "Active" : "Inactive"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;
