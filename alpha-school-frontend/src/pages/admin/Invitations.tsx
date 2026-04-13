import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Mail, Send, RefreshCw, XCircle, CheckCircle, Clock, UserPlus } from 'lucide-react';

interface Invitation {
  id: number;
  email: string;
  role: string;
  first_name: string | null;
  last_name: string | null;
  status: string;
  curriculum_level: string | null;
  classroom_id: number | null;
  created_at: string;
  expires_at: string | null;
  invited_by_name: string | null;
  invited_by_last: string | null;
}

const ROLE_OPTIONS = [
  { value: 'student', label: 'Estudiante' },
  { value: 'coach', label: 'Coach' },
  { value: 'parent', label: 'Padre/Madre' },
  { value: 'admin', label: 'Administrador' },
];

const CURRICULUM_OPTIONS = [
  { value: '4to_grado', label: '4to Grado' },
  { value: 'kinder', label: 'Kinder' },
];

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  accepted: 'bg-green-100 text-green-700',
  revoked: 'bg-red-100 text-red-700',
  expired: 'bg-gray-100 text-gray-500',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  accepted: 'Aceptada',
  revoked: 'Revocada',
  expired: 'Expirada',
};

export default function Invitations() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('student');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [curriculumLevel, setCurriculumLevel] = useState('4to_grado');
  const [classroomId, setClassroomId] = useState<number | null>(null);
  const [classrooms, setClassrooms] = useState<{ id: number; name: string; grade_name: string }[]>([]);

  const loadInvitations = async () => {
    try {
      const data = await api.get('/api/admin/invitations');
      setInvitations(data);
    } catch {
      setError('Error al cargar invitaciones');
    } finally {
      setLoading(false);
    }
  };

  const loadClassrooms = async () => {
    try {
      const data = await api.get('/api/admin/classrooms');
      setClassrooms(data);
    } catch {
      // Classrooms endpoint may not exist yet, use defaults
      setClassrooms([
        { id: 1, name: '4-A', grade_name: '4to Grado' },
        { id: 2, name: '4-B', grade_name: '4to Grado' },
        { id: 3, name: 'K-A', grade_name: 'Kinder' },
      ]);
    }
  };

  useEffect(() => {
    loadInvitations();
    loadClassrooms();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSending(true);

    try {
      const payload: Record<string, unknown> = {
        email,
        role,
        first_name: firstName || null,
        last_name: lastName || null,
      };

      if (role === 'student') {
        payload.curriculum_level = curriculumLevel;
        payload.classroom_id = classroomId;
      } else if (role === 'coach') {
        payload.classroom_id = classroomId;
      }

      await api.post('/api/admin/invitations', payload);
      setSuccess(`Invitación enviada a ${email}`);
      setEmail('');
      setFirstName('');
      setLastName('');
      setRole('student');
      setCurriculumLevel('4to_grado');
      setClassroomId(null);
      loadInvitations();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al enviar invitación');
    } finally {
      setSending(false);
    }
  };

  const handleResend = async (id: number) => {
    try {
      await api.post(`/api/admin/invitations/${id}/resend`);
      setSuccess('Invitación reenviada');
      loadInvitations();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al reenviar');
    }
  };

  const handleRevoke = async (id: number) => {
    try {
      await api.post(`/api/admin/invitations/${id}/revoke`);
      setSuccess('Invitación revocada');
      loadInvitations();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al revocar');
    }
  };

  const handleAccept = async (id: number) => {
    try {
      const result = await api.post(`/api/admin/invitations/${id}/accept`);
      setSuccess(result.message);
      loadInvitations();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error al aceptar');
    }
  };

  const filteredClassrooms = classrooms.filter(c => {
    if (role === 'student') {
      if (curriculumLevel === 'kinder') return c.grade_name === 'Kinder';
      return c.grade_name === '4to Grado';
    }
    return true;
  });

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Invitaciones</h1>
        <p className="text-gray-500">Invita nuevos usuarios a la plataforma ThriveEd</p>
      </div>

      {/* Notifications */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
          <XCircle size={16} /> {error}
          <button onClick={() => setError('')} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
          <CheckCircle size={16} /> {success}
          <button onClick={() => setSuccess('')} className="ml-auto text-green-400 hover:text-green-600">&times;</button>
        </div>
      )}

      {/* Invite Form */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm mb-8">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <UserPlus size={20} className="text-purple-600" />
          <h2 className="font-semibold text-gray-900">Nueva Invitación</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="correo@ejemplo.com"
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rol *</label>
              <select
                value={role}
                onChange={e => { setRole(e.target.value); setClassroomId(null); }}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              >
                {ROLE_OPTIONS.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input
                type="text"
                value={firstName}
                onChange={e => setFirstName(e.target.value)}
                placeholder="Nombre"
                className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input
                type="text"
                value={lastName}
                onChange={e => setLastName(e.target.value)}
                placeholder="Apellido"
                className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          {/* Conditional fields for student/coach */}
          {(role === 'student' || role === 'coach') && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              {role === 'student' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nivel Curricular</label>
                  <select
                    value={curriculumLevel}
                    onChange={e => { setCurriculumLevel(e.target.value); setClassroomId(null); }}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                  >
                    {CURRICULUM_OPTIONS.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salón</label>
                <select
                  value={classroomId ?? ''}
                  onChange={e => setClassroomId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                >
                  <option value="">Seleccionar salón...</option>
                  {filteredClassrooms.map(c => (
                    <option key={c.id} value={c.id}>{c.name} - {c.grade_name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={sending}
            className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition disabled:opacity-50"
          >
            {sending ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />}
            {sending ? 'Enviando...' : 'Enviar Invitación'}
          </button>
        </form>
      </div>

      {/* Invitations List */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Invitaciones Enviadas ({invitations.length})</h2>
          <button onClick={loadInvitations} className="text-gray-400 hover:text-gray-600 transition">
            <RefreshCw size={16} />
          </button>
        </div>
        {invitations.length === 0 ? (
          <div className="p-10 text-center text-gray-400">
            <Mail size={40} className="mx-auto mb-3 opacity-50" />
            <p>No hay invitaciones aún</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Nombre</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Rol</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Nivel</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Invitado por</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invitations.map(inv => (
                  <tr key={inv.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 text-sm font-medium text-gray-900">{inv.email}</td>
                    <td className="px-5 py-3 text-sm text-gray-600">
                      {inv.first_name || ''} {inv.last_name || ''}
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600 capitalize">
                      {ROLE_OPTIONS.find(r => r.value === inv.role)?.label || inv.role}
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600">
                      {inv.curriculum_level === 'kinder' ? 'Kinder' : inv.curriculum_level === '4to_grado' ? '4to Grado' : '-'}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${STATUS_COLORS[inv.status] || 'bg-gray-100 text-gray-500'}`}>
                        <Clock size={12} className="inline mr-1" />
                        {STATUS_LABELS[inv.status] || inv.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600">
                      {inv.invited_by_name ? `${inv.invited_by_name} ${inv.invited_by_last || ''}` : '-'}
                    </td>
                    <td className="px-5 py-3">
                      {inv.status === 'pending' && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleAccept(inv.id)}
                            className="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 transition flex items-center gap-1"
                            title="Crear cuenta ahora"
                          >
                            <CheckCircle size={12} /> Aceptar
                          </button>
                          <button
                            onClick={() => handleResend(inv.id)}
                            className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition flex items-center gap-1"
                            title="Reenviar invitación"
                          >
                            <RefreshCw size={12} /> Reenviar
                          </button>
                          <button
                            onClick={() => handleRevoke(inv.id)}
                            className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 transition flex items-center gap-1"
                            title="Revocar invitación"
                          >
                            <XCircle size={12} /> Revocar
                          </button>
                        </div>
                      )}
                      {inv.status === 'accepted' && (
                        <span className="text-xs text-green-600">Cuenta creada</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
