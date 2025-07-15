/**
 * Authentication Button - Shows login button or user menu based on auth state
 */
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { AuthModal } from "./AuthModal";
import { UserMenu } from "./UserMenu";

interface AuthButtonProps {
  onUserManagementClick?: () => void;
}

export const AuthButton = ({ onUserManagementClick }: AuthButtonProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"login" | "register">("login");
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />
        <div className="hidden md:block w-20 h-4 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <UserMenu onUserManagementClick={onUserManagementClick} />;
  }

  return (
    <>
      <div className="flex items-center space-x-3">
        <button
          onClick={() => {
            setModalMode("login");
            setIsModalOpen(true);
          }}
          className="primary-btn btn-black"
        >
          Sign In
        </button>
        <button
          onClick={() => {
            setModalMode("register");
            setIsModalOpen(true);
          }}
          className="primary-btn"
        >
          Sign Up
        </button>
      </div>

      <AuthModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialMode={modalMode}
      />
    </>
  );
};
