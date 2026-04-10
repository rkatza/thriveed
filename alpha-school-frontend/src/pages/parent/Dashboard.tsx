import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { BookOpen, Clock, Target, Star, TrendingUp, Calendar } from 'lucide-react';

export default function ParentDashboard() {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [today, setToday] = useState<any>(null);
  const [week, setWeek] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/parent/children').then(data => {
      setChildren(data);
      if (data.length > 0) {
        setSelectedChild(data[0].student_id);
        loadChildData(data[0].student_id);
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, []);

  const loadChildData = async (childId: number) => {
    setLoading(true);
    try {
      const [t, w] = await Promise.all([
        api.get(`/api/parent/child/${childId}/today`),
        api.get(`/api/parent/child/${childId}/week`),
      ]);
      setToday(t);
      setWeek(w);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const switchChild = (childId: number) => {
    setSelectedChild(childId);
    loadChildData(childId);
  };

  const child = children.find(c => c.student_id === selectedChild);

  if (loading && !today) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div></div>;

  return (
    <div>
      {/* Child selector */}
      {children.length > 1 && (
        <div className="flex gap-2 mb-6">
          {children.map(c => (
            <button key={c.student_id} onClick={() => switchChild(c.student_id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
                selectedChild === c.student_id ? 'bg-amber-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}>
              <span>{c.avatar_url || '🧒'}</span>
              {c.first_name}
            </button>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Resumen de {child?.first_name || 'tu hijo/a'}</h1>
            <p className="text-amber-100 mt-1">{child?.classroom_name || 'ThriveEd Panamá'}</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="flex items-center gap-1">
                <Star size={16} className="text-yellow-200" />
                <span className="text-xl font-bold">{today?.streak_days || 0}</span>
              </div>
              <p className="text-xs text-amber-200">Racha</p>
            </div>
            <div className="text-center">
              <span className="text-xl font-bold">{child?.overall_mastery?.toFixed(0) || 0}%</span>
              <p className="text-xs text-amber-200">Mastery</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Today's activity */}
        <div className="col-span-2 space-y-6">
          <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BookOpen size={18} /> Hoy
            </h2>
            {today?.session ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-green-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-green-600">{today.session.correct_answers}/{today.session.total_questions}</p>
                    <p className="text-sm text-gray-500">Ejercicios</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-blue-600">{Math.round((today.session.active_time_seconds || 0) / 60)} min</p>
                    <p className="text-sm text-gray-500">Tiempo activo</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-purple-600">{today.session.skill_name || '—'}</p>
                    <p className="text-sm text-gray-500">Skill actual</p>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">Progreso de la misión</span>
                    <span className="font-medium">{today.session.status === 'completed' ? 'Completada' : 'En progreso'}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-3">
                    <div className={`h-full rounded-full ${today.session.status === 'completed' ? 'bg-green-500' : 'bg-amber-400'}`}
                      style={{ width: `${today.session.total_questions > 0 ? (today.session.correct_answers / today.session.total_questions) * 100 : 0}%` }} />
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <Clock size={32} className="mx-auto mb-2" />
                <p>No hay actividad hoy aún</p>
              </div>
            )}
          </div>

          {/* Weekly summary */}
          <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar size={18} /> Esta Semana
            </h2>
            {week?.sessions && week.sessions.length > 0 ? (
              <div className="space-y-2">
                {week.sessions.map((s: any) => (
                  <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{s.mission_title}</p>
                      <p className="text-xs text-gray-500">{s.session_date} · {s.skill_name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">{s.correct_answers}/{s.total_questions}</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        s.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {s.status === 'completed' ? 'Completada' : 'En progreso'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-4">No hay sesiones esta semana</p>
            )}
          </div>
        </div>

        {/* Sidebar stats */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Target size={16} /> Mastery General
            </h3>
            <div className="text-center py-4">
              <div className="relative w-24 h-24 mx-auto">
                <svg className="w-24 h-24 -rotate-90" viewBox="0 0 36 36">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="#e5e7eb" strokeWidth="3" />
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="#f59e0b" strokeWidth="3"
                    strokeDasharray={`${child?.overall_mastery || 0}, 100`} />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold text-gray-900">{child?.overall_mastery?.toFixed(0) || 0}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <TrendingUp size={16} /> Estadísticas
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Skills dominados</span>
                <span className="font-medium">{week?.skills_mastered || 0}/32</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Sesiones completadas</span>
                <span className="font-medium">{week?.total_sessions || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Tiempo total</span>
                <span className="font-medium">{week?.total_minutes || 0} min</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
