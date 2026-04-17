import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { GraduationCap, Eye, EyeOff } from 'lucide-react';

// Demo accounts are only available in development builds. The constant is
// referenced only inside an `import.meta.env.DEV` gate, so Vite eliminates
// it from production bundles and the credentials never ship to users.
const DEMO_ACCOUNTS = import.meta.env.DEV
  ? [
      { label: 'Admin', email: 'admin@thriveed.edu.pa', password: 'admin123', icon: '👔' },
      { label: 'Coach María', email: 'coach1@thriveed.edu.pa', password: 'coach123', icon: '👩‍🏫' },
      { label: 'Sofía (4to Grado)', email: 'sofia@thriveed.edu.pa', password: 'student123', icon: '🧒' },
      { label: 'Diego (4to Grado)', email: 'diego@thriveed.edu.pa', password: 'student123', icon: '👦' },
      { label: 'Mateo (Kinder)', email: 'mateo@thriveed.edu.pa', password: 'student123', icon: '👦' },
      { label: 'Roberto (Padre)', email: 'padre.martinez@gmail.com', password: 'parent123', icon: '👨' },
    ]
  : [];

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent, demoEmail?: string, demoPassword?: string) => {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await login(demoEmail || email, demoPassword || password);
      const routes: Record<string, string> = {
        super_admin: '/admin',
        admin: '/admin',
        coach: '/coach',
        student: '/student',
        parent: '/parent',
      };
      navigate(routes[user.role] || '/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
                    <h1 className="text-3xl font-bold text-gray-900">ThriveEd</h1>
                    <p className="text-gray-500 mt-1">Piloto Panamá · Matemáticas</p>
        </div>

        {/* Login form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Correo electrónico</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition"
                placeholder="tu@correo.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition pr-12"
                  placeholder="••••••"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>
            {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {loading ? 'Ingresando...' : 'Iniciar Sesión'}
            </button>
          </form>
        </div>

        {import.meta.env.DEV && (
          <div className="mt-6 bg-white/70 backdrop-blur rounded-2xl p-6">
            <p className="text-sm font-medium text-gray-500 mb-3 text-center">Cuentas demo para probar (solo dev)</p>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_ACCOUNTS.map(acc => (
                <button
                  key={acc.email}
                  onClick={() => handleLogin(undefined, acc.email, acc.password)}
                  className="flex items-center gap-2 px-3 py-2 text-sm bg-white rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 transition text-left"
                >
                  <span className="text-lg">{acc.icon}</span>
                  <span className="text-gray-700 truncate">{acc.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
