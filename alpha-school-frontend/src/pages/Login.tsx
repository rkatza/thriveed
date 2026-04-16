import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { GraduationCap, Users, BookOpen, Heart, Shield, Loader2 } from 'lucide-react';

const ROLES = [
  {
    key: 'student_kinder',
    label: 'Estudiante',
    subtitle: 'Kinder — Mateo',
    description: 'Placement test visual con emojis y audio',
    icon: BookOpen,
    color: 'from-indigo-500 to-purple-600',
    hoverColor: 'hover:shadow-indigo-200',
    route: '/student',
  },
  {
    key: 'student_4to',
    label: 'Estudiante',
    subtitle: '4to Grado — Sofía',
    description: 'Ejercicios adaptativos con Flow Engine',
    icon: BookOpen,
    color: 'from-blue-500 to-indigo-600',
    hoverColor: 'hover:shadow-blue-200',
    route: '/student',
  },
  {
    key: 'coach',
    label: 'Coach',
    subtitle: 'María',
    description: 'Monitoreo de estudiantes y alertas',
    icon: Users,
    color: 'from-teal-500 to-emerald-600',
    hoverColor: 'hover:shadow-teal-200',
    route: '/coach',
  },
  {
    key: 'parent',
    label: 'Padre',
    subtitle: 'Roberto',
    description: 'Reportes de progreso y comunicación',
    icon: Heart,
    color: 'from-amber-500 to-orange-600',
    hoverColor: 'hover:shadow-amber-200',
    route: '/parent',
  },
  {
    key: 'admin',
    label: 'Admin',
    subtitle: 'Administrador',
    description: 'Gestión de estudiantes, coaches y currículo',
    icon: Shield,
    color: 'from-purple-500 to-pink-600',
    hoverColor: 'hover:shadow-purple-200',
    route: '/admin',
  },
];

export default function RoleSwitcher() {
  const [loadingRole, setLoadingRole] = useState<string | null>(null);
  const [error, setError] = useState('');
  const { switchRole } = useAuth();
  const navigate = useNavigate();

  const handleSwitch = async (roleKey: string, route: string) => {
    setError('');
    setLoadingRole(roleKey);
    try {
      await switchRole(roleKey);
      navigate(route);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al cambiar de rol');
    } finally {
      setLoadingRole(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-3xl mb-5 shadow-lg shadow-indigo-200">
            <GraduationCap className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900">ThriveEd</h1>
          <p className="text-gray-500 mt-2 text-lg">Piloto Panamá · Matemáticas</p>
          <p className="text-gray-400 mt-1">Selecciona un perfil para continuar</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-center">
            {error}
          </div>
        )}

        {/* Role cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ROLES.map((role) => {
            const Icon = role.icon;
            const isLoading = loadingRole === role.key;
            return (
              <button
                key={role.key}
                onClick={() => handleSwitch(role.key, role.route)}
                disabled={loadingRole !== null}
                className={`group relative bg-white rounded-2xl p-6 text-left transition-all duration-200 border border-gray-100 shadow-sm ${role.hoverColor} hover:shadow-lg hover:-translate-y-1 active:scale-[0.98] disabled:opacity-60 disabled:cursor-wait`}
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${role.color} flex items-center justify-center mb-4 shadow-md`}>
                  {isLoading ? (
                    <Loader2 className="w-7 h-7 text-white animate-spin" />
                  ) : (
                    <Icon className="w-7 h-7 text-white" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900">{role.label}</h3>
                <p className="text-sm font-medium text-gray-500 mt-0.5">{role.subtitle}</p>
                <p className="text-xs text-gray-400 mt-2 leading-relaxed">{role.description}</p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
