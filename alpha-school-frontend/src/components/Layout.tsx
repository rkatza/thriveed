import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { GraduationCap, LogOut, LayoutDashboard, Users, BookOpen, MessageSquare, BarChart3, ClipboardList, Home, Trophy, Map, User, Mail, Menu, X } from 'lucide-react';

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

  if (!user) return null;

  const navItems = NAV_ITEMS[user.role] || [];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeSidebar} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed h-full z-50 bg-white border-r border-gray-200 flex flex-col w-64
        transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:z-10
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
            <button onClick={closeSidebar} className="lg:hidden p-1 rounded-lg hover:bg-gray-100">
              <X size={20} className="text-gray-500" />
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
                onClick={closeSidebar}
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
              {user.role === 'student' ? (user as any).avatar_url || '🧒' : '👤'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.first_name} {user.last_name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition">
            <LogOut size={16} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Content */}
      <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
        {/* Mobile top bar */}
        <header className="lg:hidden sticky top-0 z-30 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-gray-100">
            <Menu size={24} className="text-gray-700" />
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 ${ROLE_COLORS[user.role]} rounded-lg flex items-center justify-center`}>
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900 text-sm">ThriveEd</span>
          </div>
          <div className="w-10" />
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
