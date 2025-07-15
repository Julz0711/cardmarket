/**
 * React Authentication Context and Provider
 */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import {
  authService,
  type User,
  type LoginCredentials,
  type RegisterData,
} from "../services/auth";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  updateProfile: (profileData: Partial<User["profile"]>) => Promise<void>;
  onAuthChange?: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
  onAuthChange?: () => void;
}

export const AuthProvider = ({ children, onAuthChange }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      const isAuth = authService.isAuthenticated();
      setIsAuthenticated(isAuth);

      if (isAuth) {
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error("Failed to get current user:", error);
          authService.logout();
          setIsAuthenticated(false);
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await authService.login(credentials);
      setUser(response.user);
      setIsAuthenticated(true);
      // Trigger data refresh after successful login
      if (onAuthChange) {
        onAuthChange();
      }
    } catch (error) {
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      const response = await authService.register(data);
      setUser(response.user);
      setIsAuthenticated(true);
      // Trigger data refresh after successful registration
      if (onAuthChange) {
        onAuthChange();
      }
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
    // Trigger data refresh after logout
    if (onAuthChange) {
      onAuthChange();
    }
  };

  const updateProfile = async (profileData: Partial<User["profile"]>) => {
    try {
      const updatedUser = await authService.updateProfile(profileData);
      setUser(updatedUser);
    } catch (error) {
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: isAuthenticated && !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
        onAuthChange,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
