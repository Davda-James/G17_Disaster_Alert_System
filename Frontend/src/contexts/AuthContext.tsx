import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Shared User Interface
export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  location: {
    city: string;
    state: string;
  };
  isAuthorized: boolean;
  notificationPreferences: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  coordinates: {
    lat: number;
    lng: number;
  };
}

interface SignupData {
  name: string;
  email: string;
  phone: string;
  city: string;
  state: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (data: SignupData) => Promise<boolean>;
  logout: () => void;
  updateUser: (data: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Flask runs on port 5000 by default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize token directly so it's available immediately on reload
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // 1. Check for existing session on refresh
  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const response = await fetch(`${API_URL}/me`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          
          if (response.ok) {
            const data = await response.json();
            setUser(data.user);
          } else {
            // Token invalid - clear state and storage
            localStorage.removeItem('token');
            setToken(null); 
            setUser(null);
          }
        } catch (error) {
          console.error('Session verification failed', error);
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    verifyToken();
  }, []); // Run once on mount

  // 2. Login
  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      localStorage.setItem('token', data.token);
      setToken(data.token); // FIX: Update token state
      setUser(data.user);
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  // 3. Signup
  const signup = async (data: SignupData): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) return false;

      const responseData = await response.json();
      localStorage.setItem('token', responseData.token);
      setToken(responseData.token); // FIX: Update token state
      setUser(responseData.user);
      return true;
    } catch (error) {
      console.error('Signup error:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null); // FIX: Update token state
    setUser(null);
  };

  // 4. Update User
  const updateUser = async (data: Partial<User>) => {
    if (!user) return;
    try {
      // Use state token instead of reading localStorage again
      const response = await fetch(`${API_URL}/user/${user.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Update failed:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      // FIX: Check 'token' for instant authentication state (prevents reload flicker)
      isAuthenticated: !!token, 
      isLoading,
      login, 
      signup, 
      logout, 
      updateUser 
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}