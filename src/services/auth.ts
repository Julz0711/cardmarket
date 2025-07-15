/**
 * Authentication service for CardMarket app
 * Handles login, registration, token management, and user state
 */

export interface User {
  user_id: string;
  username: string;
  email: string;
  profile?: {
    display_name?: string;
    bio?: string;
    avatar_url?: string;
  };
  created_at?: string;
  last_login?: string;
}

export interface AuthResponse {
  message: string;
  token: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

class AuthService {
  private baseUrl = "http://localhost:5000/api/auth";
  private tokenKey = "cardmarket_token";
  private userKey = "cardmarket_user";

  /**
   * Get stored authentication token
   */
  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  /**
   * Get stored user information
   */
  getUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Check if token is expired (basic check)
      const payload = JSON.parse(atob(token.split(".")[1]));
      const now = Date.now() / 1000;
      return payload.exp > now;
    } catch {
      return false;
    }
  }

  /**
   * Set authentication data
   */
  private setAuthData(token: string, user: User): void {
    localStorage.setItem(this.tokenKey, token);
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  /**
   * Clear authentication data
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  /**
   * Get authorization headers for API requests
   */
  getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Registration failed");
    }

    this.setAuthData(result.token, result.user);
    return result;
  }

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Login failed");
    }

    this.setAuthData(result.token, result.user);
    return result;
  }

  /**
   * Logout user
   */
  logout(): void {
    this.clearAuthData();
  }

  /**
   * Get current user from server
   */
  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/me`, {
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Failed to get user");
    }

    // Update stored user data
    this.setAuthData(this.getToken()!, result.user);
    return result.user;
  }

  /**
   * Update user profile
   */
  async updateProfile(profileData: Partial<User["profile"]>): Promise<User> {
    const response = await fetch(`${this.baseUrl}/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify(profileData),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Failed to update profile");
    }

    // Update stored user data
    this.setAuthData(this.getToken()!, result.user);
    return result.user;
  }
}

// Create singleton instance
export const authService = new AuthService();
