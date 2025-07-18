/**
 * Authentication Modal Component
 */
import { useState } from "react";
import { LoginForm, RegisterForm } from "./AuthForms";
import CloseIcon from "@mui/icons-material/Close";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: "login" | "register";
}

export const AuthModal = ({
  isOpen,
  onClose,
  initialMode = "login",
}: AuthModalProps) => {
  const [mode, setMode] = useState<"login" | "register">(initialMode);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-primary flex items-center justify-center p-4 z-50">
      <div className="bg-secondary rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto border border-primary">
        <div className="flex justify-between items-center p-6 border-b border-primary">
          <div className="text-[1.5rem] font-semibold text-white">
            {mode === "login" ? "Welcome Back" : "Join Portfolio Manager"}
          </div>
          <button
            onClick={onClose}
            className="primary-btn btn-black flex items-center justify-center text-gray-400 w-8 h-8 hover:text-gray-200 font-light"
          >
            <CloseIcon className="p-1" />
          </button>
        </div>

        <div className="p-6">
          {mode === "login" ? (
            <LoginForm
              onSwitchToRegister={() => setMode("register")}
              onClose={onClose}
            />
          ) : (
            <RegisterForm
              onSwitchToLogin={() => setMode("login")}
              onClose={onClose}
            />
          )}
        </div>
      </div>
    </div>
  );
};
