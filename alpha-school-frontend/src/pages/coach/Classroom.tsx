import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, HelpCircle, Pause, Play, Eye, Siren, TrendingDown, Star, Trophy, BarChart3 } from 'lucide-react';

const STATUS_COLORS: Record<string, { bg: string; ring: string; label: string }> = {
  green: { bg: 'bg-green-400', ring: 'ring-green-200', label: 'Trabajando bien' },
  yellow: { bg: 'bg-amber-400', ring: 'ring-amber-200', label: 'Necesita atención' },
  red: { bg: 'bg-red-400', ring: 'ring-red-200', label: 'En dificultad' },
  gray: { bg: 'bg-gray-300', ring: 'ring-gray-200', label: 'Inactivo' },
};

interface AlertData {
  rescue_alerts: any[];
  struggling_students: any[];
  star_students: any[];
  intervention_suggestions: any[];
  total_alerts: number;
}

interface InsightsData {
  leaderboard: any[];
  skill_gaps: any[];
}

export default function CoachClassroom() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [helpRequests, setHelpRequests] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<AlertData | null>(null);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [showInsights, setShowInsights] = useState(false);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      const [classroom, helps, alertsData, insightsData] = await Promise.all([
        api.get('/api/coach/classroom/live'),
        api.get('/api/coach/help-requests'),
        api.get('/api/coach/alerts').catch(() => null),
        api.get('/api/coach/classroom/insights').catch(() => null),
      ]);
      setData({
        classroom_name: classroom.classroom?.name || 'Mi Salón',
        students: (classroom.students || []).map((s: any) => ({
          ...s,
          student_id: s.id || s.student_id,
          status: s.indicator || s.status || 'gray',
          current_skill: s.skill_name || s.current_skill || null,
          session_progress: s.total_questions ? (s.correct_answers / s.total_questions) : 0,
          time_active: s.active_time_seconds ? Math.round(s.active_time_seconds / 60) : 0,
          needs_help: s.help_request_id != null,
        })),
      });
      setHelpRequests(helps);
      if (alertsData) setAlerts(alertsData);
      if (insightsData) setInsights(insightsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const togglePause = async (studentId: number, isPaused: boolean) => {
    try {
      if (isPaused) {
        await api.post(`/api/coach/student/${studentId}/resume`);
      } else {
        await api.post(`/api/coach/student/${studentId}/pause`);
      }
      loadData();
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mi Salón en Vivo</h1>
          <p className="text-gray-500">· {data.students?.length || 0} estudiantes</p>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => setShowInsights(!showInsights)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition
              ${showInsights ? 'bg-teal-600 text-white' : 'bg-teal-50 text-teal-700 hover:bg-teal-100'}`}>
            <BarChart3 size={14} /> Insights
          </button>
          {Object.entries(STATUS_COLORS).map(([key, val]) => (
            <div key={key} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${val.bg}`} />
              <span className="text-xs text-gray-500">{val.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Rescue Mode Alerts Banner */}
      {alerts && alerts.rescue_alerts.length > 0 && (
        <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Siren size={20} className="text-red-600" />
            <h3 className="font-bold text-red-800">Modo Rescate ({alerts.rescue_alerts.length} estudiante{alerts.rescue_alerts.length > 1 ? 's' : ''})</h3>
          </div>
          <div className="space-y-2">
            {alerts.intervention_suggestions
              .filter(s => s.type === 'rescue')
              .map((suggestion, i) => (
              <div key={i} className="flex items-center justify-between bg-white p-3 rounded-lg border border-red-200">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                      suggestion.severity === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {suggestion.severity === 'high' ? 'URGENTE' : 'ATENCIÓN'}
                    </span>
                    <span className="text-sm font-semibold text-gray-900">{suggestion.student_name}</span>
                  </div>
                  <p className="text-sm text-red-700 mt-1">{suggestion.message}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{suggestion.suggestion}</p>
                  {suggestion.skill && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                      {suggestion.skill}
                    </span>
                  )}
                </div>
                <button onClick={() => navigate(`/coach/student/${suggestion.student_id}`)}
                  className="ml-3 px-3 py-1.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition">
                  Intervenir
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Struggling Students Alert */}
      {alerts && alerts.struggling_students.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown size={18} className="text-amber-600" />
            <h3 className="font-semibold text-amber-800">Estudiantes con Dificultad ({alerts.struggling_students.length})</h3>
          </div>
          <div className="space-y-2">
            {alerts.intervention_suggestions
              .filter(s => s.type === 'low_accuracy')
              .map((suggestion, i) => (
              <div key={i} className="flex items-center justify-between bg-white p-3 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-gray-900">{suggestion.student_name}</span>
                  <span className="text-sm text-amber-700 ml-2">{suggestion.message}</span>
                  <p className="text-xs text-gray-500 mt-0.5">{suggestion.suggestion}</p>
                </div>
                <button onClick={() => navigate(`/coach/student/${suggestion.student_id}`)}
                  className="text-sm text-teal-600 hover:text-teal-800 font-medium">
                  Ver
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Star Students */}
      {alerts && alerts.star_students.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Star size={18} className="text-green-600" />
            <h3 className="font-semibold text-green-800">Estudiantes Destacados ({alerts.star_students.length})</h3>
          </div>
          <div className="flex gap-3 overflow-x-auto">
            {alerts.star_students.map((s, i) => (
              <div key={i} className="flex items-center gap-2 bg-white px-3 py-2 rounded-lg min-w-fit">
                <span>{s.avatar_url || '&#x1F9D2;'}</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">{s.first_name}</p>
                  <p className="text-xs text-green-600">{s.accuracy}% preciso · Nivel {s.level || 1}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help requests banner */}
      {helpRequests.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <HelpCircle size={18} className="text-amber-600" />
            <h3 className="font-semibold text-amber-800">Solicitudes de Ayuda ({helpRequests.length})</h3>
          </div>
          <div className="space-y-2">
            {helpRequests.map((hr: any) => (
              <div key={hr.id} className="flex items-center justify-between bg-white p-3 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-gray-900">{hr.student_name}</span>
                  <span className="text-sm text-gray-500 ml-2">{hr.message}</span>
                </div>
                <button onClick={() => navigate(`/coach/student/${hr.student_id}`)}
                  className="text-sm text-teal-600 hover:text-teal-800 font-medium">
                  Atender
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights Panel */}
      {showInsights && insights && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Leaderboard */}
          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Trophy size={16} className="text-amber-500" /> Tabla de Posiciones
            </h3>
            <div className="space-y-2">
              {insights.leaderboard.slice(0, 5).map((s) => (
                <div key={s.student_id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
                  <span className={`text-lg font-bold w-6 text-center ${
                    s.rank === 1 ? 'text-amber-500' : s.rank === 2 ? 'text-gray-400' : s.rank === 3 ? 'text-amber-700' : 'text-gray-300'
                  }`}>
                    {s.rank}
                  </span>
                  <span className="text-lg">{s.avatar || '&#x1F9D2;'}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.level_icon} {s.level_title} · Racha {s.streak_days}d</p>
                  </div>
                  <span className="text-sm font-bold text-indigo-600">{s.total_xp} XP</span>
                </div>
              ))}
            </div>
          </div>

          {/* Skill Gaps */}
          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <TrendingDown size={16} className="text-red-500" /> Skills con Menor Dominio
            </h3>
            <div className="space-y-2">
              {insights.skill_gaps.slice(0, 6).map((s, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.students_mastered || 0} estudiantes dominan</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-100 rounded-full h-2">
                      <div className="h-full bg-red-400 rounded-full" style={{ width: `${s.avg_mastery || 0}%` }} />
                    </div>
                    <span className="text-xs font-medium text-gray-600 w-10 text-right">{s.avg_mastery || 0}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Student grid */}
      <div className="grid grid-cols-4 gap-4">
        {(data.students || []).map((s: any) => {
          const status = STATUS_COLORS[s.status] || STATUS_COLORS.gray;
          const isRescue = alerts?.rescue_alerts.some(r => r.student_id === s.student_id);
          return (
            <div key={s.student_id} className={`bg-white rounded-xl p-5 border shadow-sm ring-2 ${
              isRescue ? 'ring-red-400 border-red-200' : `${status.ring} border-gray-100`
            } transition hover:shadow-md`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${isRescue ? 'bg-red-500 animate-pulse' : status.bg}`} />
                  <span className="text-lg">{s.avatar_url || '&#x1F9D2;'}</span>
                </div>
                <div className="flex items-center gap-1">
                  {isRescue && <Siren size={16} className="text-red-500" />}
                  {s.needs_help && <HelpCircle size={16} className="text-amber-500" />}
                  {s.status === 'red' && !isRescue && <AlertTriangle size={16} className="text-red-500" />}
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 text-sm">{s.first_name} {s.last_name}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{s.current_skill || 'Sin actividad'}</p>
              {isRescue && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                  Modo Rescate
                </span>
              )}

              <div className="mt-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400">Progreso</p>
                  <div className="flex items-center gap-1 mt-0.5">
                    <div className="w-16 bg-gray-100 rounded-full h-2">
                      <div className="h-full bg-teal-500 rounded-full" style={{ width: `${(s.session_progress || 0) * 100}%` }} />
                    </div>
                    <span className="text-xs text-gray-500">{((s.session_progress || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <span className="text-xs text-gray-500">{s.time_active || 0} min</span>
              </div>

              <div className="flex gap-1 mt-3">
                <button onClick={() => navigate(`/coach/student/${s.student_id}`)}
                  className={`flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs font-medium transition
                    ${isRescue ? 'bg-red-50 text-red-700 hover:bg-red-100' : 'bg-teal-50 text-teal-700 hover:bg-teal-100'}`}>
                  <Eye size={12} /> {isRescue ? 'Intervenir' : 'Detalle'}
                </button>
                <button onClick={() => togglePause(s.student_id, s.is_paused)}
                  className="flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-50 text-gray-600 rounded-lg text-xs hover:bg-gray-100 transition">
                  {s.is_paused ? <Play size={12} /> : <Pause size={12} />}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
