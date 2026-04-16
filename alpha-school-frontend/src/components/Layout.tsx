import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { GraduationCap, ArrowLeftRight, LayoutDashboard, Users, BookOpen, MessageSquare, BarChart3, ClipboardList, Home, Trophy, Map, User, Mail, Menu, X } from 'lucide-react';

const NAV_ITEMS: Record<string, { label: string; path: string; icon: React.ReactNode }[]> = {
  super_admin: [
    { label: 'Dashboard', path: '/admin', icon: <LayoutDashboard size={20} /> },
    { label: 'Estudiantes', path: '/admin/students', icon: <Users size={20} /> },
    { label: 'Coaches', path: '/admin/coaches', icon: <User size={20} /> },
    { label: 'Padres', path: '/admin/parents', icon: <Users size={20} /> },
    { label: 'Currículo', path: '/admin/curriculum', icon: <BookOpen size={20} /> },
    { label: 'Invitaciones', path: '/admin/invitations', icon: <Mail size={20} /> },
    { label: 'Auditoría', path: '/admin/audit', icon: <ClipboardList size={20} /> },
  ],
  admin: [
    { label: 'Dashboard', path: '/admin', icon: <LayoutDashboard size={20} /> },
    { label: 'Estudiantes', path: '/admin/students', icon: <Users size={20} /> },
    { label: 'Coaches', path: '/admin/coaches', icon: <User size={20} /> },
    { label: 'Currículo', path: '/admin/curriculum', icon: <BookOpen size={20} /> },
    { label: 'Invitaciones', path: '/admin/invitations', icon: <Mail size={20} /> },
  ],
  coach: [
    { label: 'Mi Salón', path: '/coach', icon: <LayoutDashboard size={20} /> },
    { label: 'Resumen del Día', path: '/coach/summary', icon: <BarChart3 size={20} /> },
    { label: 'Mensajes', path: '/coach/messages', icon: <MessageSquare size={20} /> },
  ],
  student: [
    { label: 'Mi Misión', path: '/student', icon: <Home size={20} /> },
    { label: 'Progreso', path: '/student/progress', icon: <BarChart3 size={20} /> },
    { label: 'Mapa de Skills', path: '/student/skills', icon: <Map size={20} /> },
    { label: 'Logros', path: '/student/achievements', icon: <Trophy size={20} /> },
  ],
  parent: [
    { label: 'Resumen', path: '/parent', icon: <Home size={20} /> },
    { label: 'Mapa de Skills', path: '/parent/skills', icon: <Map size={20} /> },
    { label: 'Mensajes', path: '/parent/messages', icon: <MessageSquare size={20} /> },
  ],
};

const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Administrador',
  admin: 'Administrador',
  coach: 'Coach',
  student: 'Estudiante',
  parent: 'Padre/Madre',
};

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-purple-600',
  admin: 'bg-purple-600',
  coach: 'bg-teal-600',
  student: 'bg-indigo-600',
  parent: 'bg-amber-600',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Close sidebar on escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSidebarOpen(false);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  if (!user) return null;

  const navItems = NAV_ITEMS[user.role] || [];

  const handleSwitchProfile = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile top bar */}
      <div className="fixed top-0 left-0 right-0 h-14 bg-white border-b border-gray-200 flex items-center px-4 z-30 md:hidden">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 -ml-2 rounded-lg text-gray-600 hover:bg-gray-100 transition"
          aria-label="Abrir menú"
        >
          <Menu size={24} />
        </button>
        <div className="flex items-center gap-2 ml-3">
          <div className={`w-7 h-7 ${ROLE_COLORS[user.role]} rounded-lg flex items-center justify-center`}>
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-gray-900 text-sm">ThriveEd</span>
        </div>
      </div>

      {/* Overlay (mobile only) */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full z-50
        transition-transform duration-300 ease-in-out
        md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo + close button */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 ${ROLE_COLORS[user.role]} rounded-xl flex items-center justify-center`}>
                <GraduationCap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-gray-900 text-sm">ThriveEd</h1>
                <span className="text-xs text-gray-500">{ROLE_LABELS[user.role]}</span>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition md:hidden"
              aria-label="Cerrar menú"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition
                  ${isActive ? `${ROLE_COLORS[user.role]} text-white` : 'text-gray-600 hover:bg-gray-100'}`}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 bg-gray-100 rounded-full flex items-center justify-center text-lg">
              {user.role === 'student' ? user.avatar_url || '🧒' : '👤'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.first_name} {user.last_name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleSwitchProfile}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-indigo-600 hover:bg-indigo-50 rounded-lg transition">
            <ArrowLeftRight size={16} />
            Cambiar perfil
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 md:ml-64 pt-14 md:pt-0 p-4 sm:pt-14 sm:px-6 sm:pb-6 md:p-8">
        {children}
      </main>
    </div>
  );
}
