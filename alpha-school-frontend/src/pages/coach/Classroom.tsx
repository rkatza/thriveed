import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, HelpCircle, Pause, Play, Eye } from 'lucide-react';

const STATUS_COLORS: Record<string, { bg: string; ring: string; label: string }> = {
  green: { bg: 'bg-green-400', ring: 'ring-green-200', label: 'Trabajando bien' },
  yellow: { bg: 'bg-amber-400', ring: 'ring-amber-200', label: 'Necesita atención' },
  red: { bg: 'bg-red-400', ring: 'ring-red-200', label: 'En dificultad' },
  gray: { bg: 'bg-gray-300', ring: 'ring-gray-200', label: 'Inactivo' },
};

export default function CoachClassroom() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [helpRequests, setHelpRequests] = useState<any[]>([]);
  const navigate = useNavigate();

  const loadData = async () => {
    try {
      const [classroom, helps] = await Promise.all([
        api.get('/api/coach/classroom/live'),
        api.get('/api/coach/help-requests'),
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
          {Object.entries(STATUS_COLORS).map(([key, val]) => (
            <div key={key} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${val.bg}`} />
              <span className="text-xs text-gray-500">{val.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Help requests banner */}
      {helpRequests.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
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

      {/* Student grid */}
      <div className="grid grid-cols-4 gap-4">
        {(data.students || []).map((s: any) => {
          const status = STATUS_COLORS[s.status] || STATUS_COLORS.gray;
          return (
            <div key={s.student_id} className={`bg-white rounded-xl p-5 border border-gray-100 shadow-sm ring-2 ${status.ring} transition hover:shadow-md`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${status.bg}`} />
                  <span className="text-lg">{s.avatar_url || '🧒'}</span>
                </div>
                {s.needs_help && <HelpCircle size={16} className="text-amber-500" />}
                {s.status === 'red' && <AlertTriangle size={16} className="text-red-500" />}
              </div>
              <h3 className="font-semibold text-gray-900 text-sm">{s.first_name} {s.last_name}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{s.current_skill || 'Sin actividad'}</p>

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
                  className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-teal-50 text-teal-700 rounded-lg text-xs font-medium hover:bg-teal-100 transition">
                  <Eye size={12} /> Detalle
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
