import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { BarChart3, TrendingUp, Clock, Target, Star } from 'lucide-react';

export default function StudentProgress() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/student/progress').then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mi Progreso</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center mb-3">
            <Target size={20} className="text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.skills_mastered || 0}</p>
          <p className="text-sm text-gray-500">Skills dominados</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-3">
            <TrendingUp size={20} className="text-green-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.overall_mastery?.toFixed(0) || 0}%</p>
          <p className="text-sm text-gray-500">Mastery general</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center mb-3">
            <Star size={20} className="text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.total_xp || 0}</p>
          <p className="text-sm text-gray-500">XP total</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
            <Clock size={20} className="text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{data.total_time_minutes || 0}</p>
          <p className="text-sm text-gray-500">Minutos totales</p>
        </div>
      </div>

      {/* Mastery by skill */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mb-6">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <BarChart3 size={18} /> Mastery por Skill
        </h2>
        <div className="space-y-3">
          {(data.mastery_by_skill || []).map((s: any) => (
            <div key={s.skill_id} className="flex items-center gap-3">
              <span className="text-sm text-gray-600 w-24 sm:w-48 truncate">{s.skill_name}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                <div className={`h-full rounded-full transition-all flex items-center justify-end pr-2
                  ${s.mastery_level >= 0.9 ? 'bg-green-500' : s.mastery_level >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                  style={{ width: `${Math.max(s.mastery_level * 100, 5)}%` }}>
                  {s.mastery_level >= 0.15 && (
                    <span className="text-xs text-white font-medium">{(s.mastery_level * 100).toFixed(0)}%</span>
                  )}
                </div>
              </div>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                s.mastery_level >= 0.9 ? 'bg-green-100 text-green-700' :
                s.mastery_level >= 0.5 ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              }`}>
                {s.mastery_level >= 0.9 ? 'Dominado' : s.mastery_level >= 0.5 ? 'En progreso' : 'Iniciando'}
              </span>
            </div>
          ))}
          {(!data.mastery_by_skill || data.mastery_by_skill.length === 0) && (
            <p className="text-sm text-gray-400 text-center py-4">Completa ejercicios para ver tu progreso aquí</p>
          )}
        </div>
      </div>

      {/* Recent sessions */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
        <h2 className="font-semibold text-gray-900 mb-4">Sesiones Recientes</h2>
        <div className="space-y-3">
          {(data.recent_sessions || []).map((s: any) => (
            <div key={s.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-gray-50 rounded-lg gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{s.mission_title}</p>
                <p className="text-xs text-gray-500">{s.session_date} · {s.skill_name}</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-sm font-medium text-gray-700">{s.correct_answers}/{s.total_questions}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  s.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {s.status === 'completed' ? 'Completada' : 'En progreso'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
