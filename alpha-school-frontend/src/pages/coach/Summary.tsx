import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { BarChart3, Users, Target, Clock, TrendingUp } from 'lucide-react';

export default function CoachSummary() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/coach/daily-summary').then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return null;

  const summary = data.summary || {};
  const sessions = data.sessions || [];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Resumen del Día</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-teal-100 rounded-lg flex items-center justify-center mb-3">
            <Users size={20} className="text-teal-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{summary.total_students || 0}</p>
          <p className="text-sm text-gray-500">Estudiantes</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-3">
            <Target size={20} className="text-green-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{summary.completed || 0}</p>
          <p className="text-sm text-gray-500">Sesiones completadas</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center mb-3">
            <Clock size={20} className="text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{summary.avg_time_minutes?.toFixed(0) || 0} min</p>
          <p className="text-sm text-gray-500">Tiempo promedio</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
            <TrendingUp size={20} className="text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{summary.avg_accuracy?.toFixed(0) || 0}%</p>
          <p className="text-sm text-gray-500">Precisión promedio</p>
        </div>
      </div>

      {/* Student performance */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2"><BarChart3 size={18} /> Rendimiento por Estudiante</h2>
        </div>
        <div className="overflow-x-auto">
        <table className="w-full min-w-[600px]">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estudiante</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Misión</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Progreso</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Precisión</th>
              <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sessions.map((s: any) => {
              const accuracy = s.total_questions ? Math.round((s.correct_answers / s.total_questions) * 100) : 0;
              const progress = s.total_questions ? (s.correct_answers / s.total_questions) : 0;
              return (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span>🧒</span>
                      <span className="text-sm font-medium text-gray-900">{s.first_name} {s.last_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600">{s.skill_name || s.mission_title || '—'}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-gray-100 rounded-full h-2">
                        <div className="h-full bg-teal-500 rounded-full" style={{ width: `${progress * 100}%` }} />
                      </div>
                      <span className="text-xs text-gray-500">{s.correct_answers}/{s.total_questions}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600">{accuracy}%</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      s.status === 'completed' ? 'bg-green-100 text-green-700' :
                      s.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {s.status === 'completed' ? 'Completado' : s.status === 'in_progress' ? 'En progreso' : 'Sin sesión'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
