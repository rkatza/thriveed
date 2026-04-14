import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useNavigate } from 'react-router-dom';
import { Search, Eye, Plus, X, Loader2 } from 'lucide-react';

export default function AdminStudents() {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', password: '',
    age: 5, classroom_id: 1, interests: '', curriculum_level: 'kinder'
  });
  const navigate = useNavigate();

  const loadStudents = () => {
    api.get('/api/admin/students').then(setStudents).finally(() => setLoading(false));
  };

  useEffect(() => { loadStudents(); }, []);

  const filtered = students.filter(s =>
    `${s.first_name} ${s.last_name} ${s.email}`.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    setCreating(true);
    try {
      await api.post('/api/admin/students', form);
      setShowCreate(false);
      setForm({ first_name: '', last_name: '', email: '', password: '', age: 5, classroom_id: 1, interests: '', curriculum_level: 'kinder' });
      loadStudents();
    } catch (err: any) {
      alert(err.message || 'Error al crear estudiante');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Estudiantes</h1>
        <div className="flex gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Buscar..."
              className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
            <Plus size={16} /> Crear Estudiante
          </button>
        </div>
      </div>

      {/* Create Student Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Crear Estudiante</h2>
              <button onClick={() => setShowCreate(false)} className="p-1 text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">Nombre</label>
                  <input value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})}
                    className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" placeholder="Nombre" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">Apellido</label>
                  <input value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})}
                    className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" placeholder="Apellido" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Email</label>
                <input value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                  className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" placeholder="email@ejemplo.com" type="email" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Contraseña</label>
                <input value={form.password} onChange={e => setForm({...form, password: e.target.value})}
                  className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" placeholder="Contraseña temporal" type="password" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">Edad</label>
                  <input type="number" value={form.age} onChange={e => setForm({...form, age: parseInt(e.target.value) || 5})}
                    className="w-full p-2.5 border border-gray-200 rounded-lg text-sm" min={4} max={15} />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 mb-1 block">Nivel</label>
                  <select value={form.curriculum_level} onChange={e => setForm({...form, curriculum_level: e.target.value})}
                    className="w-full p-2.5 border border-gray-200 rounded-lg text-sm bg-white">
                    <option value="kinder">Kinder (5-6 años)</option>
                    <option value="4to_grado">4to Grado (9-10 años)</option>
                  </select>
                </div>
              </div>
              <button onClick={handleCreate} disabled={creating || !form.first_name || !form.email || !form.password}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition disabled:opacity-50">
                {creating ? <Loader2 className="animate-spin mx-auto" size={20} /> : 'Crear Estudiante'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estudiante</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Salón</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Edad</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Placement Test</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map(s => (
              <tr key={s.id} className="hover:bg-gray-50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{s.avatar_url}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{s.first_name} {s.last_name}</p>
                      <p className="text-xs text-gray-500">{s.nickname}</p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3 text-sm text-gray-600">{s.email}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{s.classroom_name || '—'}</td>
                <td className="px-5 py-3 text-sm text-gray-600">{s.age} años</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${s.placement_test_completed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {s.placement_test_completed ? `${s.placement_test_score?.toFixed(0)}%` : 'Pendiente'}
                  </span>
                </td>
                <td className="px-5 py-3">
                  <button onClick={() => navigate(`/admin/students/${s.id}`)}
                    className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800">
                    <Eye size={14} /> Ver detalle
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
