import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from './api';

interface User {
  id: number;
  email: string;
  role: string;
  first_name: string;
  last_name: string;
  student_id?: number;
  coach_id?: number;
  parent_id?: number;
  classroom_id?: number;
  nickname?: string;
  avatar_url?: string;
  placement_test_completed?: boolean;
  interests?: string;
  age?: number;
  curriculum_level?: string;
}

// Default accounts per role — used for auto-login when switching roles
const ROLE_ACCOUNTS: Record<string, { email: string; password: string }> = {
  admin: { email: 'admin@thriveed.edu.pa', password: 'admin123' },
  coach: { email: 'coach1@thriveed.edu.pa', password: 'coach123' },
  student_kinder: { email: 'mateo@thriveed.edu.pa', password: 'student123' },
  student_4to: { email: 'sofia@thriveed.edu.pa', password: 'student123' },
  parent: { email: 'padre.martinez@gmail.com', password: 'parent123' },
};

interface AuthContextType {
  user: User | null;
  token: string | null;
  switchRole: (roleKey: string) => Promise<User>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  switchRole: async () => { throw new Error('Not implemented'); },
  logout: () => {},
  loading: true,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const switchRole = async (roleKey: string) => {
    const account = ROLE_ACCOUNTS[roleKey];
    if (!account) throw new Error(`No account configured for role: ${roleKey}`);
    const data = await api.post('/api/auth/login', { email: account.email, password: account.password });
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, switchRole, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
