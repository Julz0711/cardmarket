/**
 * User Menu Component - Shows user info and logout option
 */
import { useAuth } from "../../contexts/AuthContext";
import PersonIcon from "@mui/icons-material/Person";

interface UserMenuProps {
  onUserManagementClick?: () => void;
}

export const UserMenu = ({ onUserManagementClick }: UserMenuProps) => {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) return null;

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="flex items-center space-x-3">
      {/* User Management button */}
      {onUserManagementClick && (
        <button
          onClick={onUserManagementClick}
          className="primary-btn btn-black flex items-center gap-1"
          title="User Management"
        >
          <PersonIcon fontSize="small" />
          <span className="hidden sm:inline">Users</span>
        </button>
      )}
      {/* User avatar and name */}
      <div className="flex items-center space-x-3 bg-secondary rounded-lg px-4 py-2 border border-gray-600">
        {/* User avatar */}
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
          {user.profile?.display_name?.[0] || user.username[0].toUpperCase()}
        </div>

        {/* Username display */}
        <span className="text-sm font-medium text-white min-w-0">
          {user.profile?.display_name || user.username}
        </span>

        {/* Logout button */}
        <button onClick={handleLogout} className="primary-btn btn-black">
          Logout
        </button>
      </div>
    </div>
  );
};
