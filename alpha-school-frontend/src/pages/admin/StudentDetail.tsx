import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { ArrowLeft, Trophy, BookOpen, Target } from 'lucide-react';

export default function StudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/api/admin/students/${id}`).then(setData).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return <p>Estudiante no encontrado</p>;

  const { student, mastery, sessions, achievements, interventions } = data;
  const interests = JSON.parse(student.interests || '[]');

  return (
    <div>
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Volver
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mb-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <span className="text-4xl">{student.avatar_url}</span>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-gray-900">{student.first_name} {student.last_name}</h1>
            <p className="text-gray-500 text-sm sm:text-base">{student.email} · {student.age} años · {student.classroom_name || 'Sin salón'}</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              {interests.map((i: string) => (
                <span key={i} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs">{i}</span>
              ))}
            </div>
          </div>
          <div className="sm:ml-auto text-left sm:text-right">
            <p className="text-sm text-gray-500">Placement Test</p>
            <p className={`text-2xl font-bold ${student.placement_test_completed ? 'text-green-600' : 'text-gray-400'}`}>
              {student.placement_test_completed ? `${student.placement_test_score?.toFixed(0)}%` : 'Pendiente'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Mastery Map */}
        <div className="lg:col-span-2 bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Target size={18} /> Mapa de Mastery</h2>
          <div className="space-y-2">
            {mastery.map((m: any) => (
              <div key={m.skill_id} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-24 sm:w-32 truncate">{m.skill_name}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${m.mastery_level >= 0.9 ? 'bg-green-500' : m.mastery_level >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                    style={{ width: `${m.mastery_level * 100}%` }} />
                </div>
                <span className="text-xs font-medium w-12 text-right">{(m.mastery_level * 100).toFixed(0)}%</span>
              </div>
            ))}
            {mastery.length === 0 && <p className="text-sm text-gray-400">Sin datos de mastery aún</p>}
          </div>
        </div>

        {/* Achievements */}
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Trophy size={18} /> Logros</h2>
          <div className="space-y-3">
            {achievements.map((a: any) => (
              <div key={a.id} className="flex items-center gap-3 p-2 bg-amber-50 rounded-lg">
                <span className="text-2xl">{a.icon}</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">{a.title}</p>
                  <p className="text-xs text-gray-500">{a.description}</p>
                </div>
              </div>
            ))}
            {achievements.length === 0 && <p className="text-sm text-gray-400">Sin logros aún</p>}
          </div>
        </div>
      </div>

      {/* Sessions */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mt-6">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><BookOpen size={18} /> Historial de Sesiones</h2>
        <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Fecha</th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Misión</th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Skill</th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Estado</th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Resultado</th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Tiempo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sessions.map((s: any) => (
              <tr key={s.id}>
                <td className="px-4 py-2 text-sm text-gray-600">{s.session_date}</td>
                <td className="px-4 py-2 text-sm text-gray-900">{s.mission_title}</td>
                <td className="px-4 py-2 text-sm text-gray-600">{s.skill_name}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${s.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                    {s.status === 'completed' ? 'Completada' : 'En progreso'}
                  </span>
                </td>
                <td className="px-4 py-2 text-sm text-gray-600">{s.correct_answers}/{s.total_questions}</td>
                <td className="px-4 py-2 text-sm text-gray-600">{Math.round(s.active_time_seconds / 60)} min</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>

      {/* Interventions */}
      {interventions.length > 0 && (
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mt-6">
          <h2 className="font-semibold text-gray-900 mb-4">Intervenciones del Coach</h2>
          <div className="space-y-3">
            {interventions.map((i: any) => (
              <div key={i.id} className="p-3 bg-amber-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs font-medium">{i.tag}</span>
                  <span className="text-xs text-gray-500">por {i.coach_name}</span>
                </div>
                {i.notes && <p className="text-sm text-gray-700">{i.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
