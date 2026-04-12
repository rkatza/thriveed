import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { BookOpen, Clock, Target, Star, TrendingUp, Calendar, Download, BarChart3, Trophy } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ParentDashboard() {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [today, setToday] = useState<any>(null);
  const [week, setWeek] = useState<any>(null);
  const [monthlyReport, setMonthlyReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showMonthly, setShowMonthly] = useState(false);

  useEffect(() => {
    api.get('/api/parent/children').then(data => {
      setChildren(data);
      if (data.length > 0) {
        setSelectedChild(data[0].id);
        loadChildData(data[0].id);
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, []);

  const loadChildData = async (childId: number) => {
    setLoading(true);
    try {
      const [t, w, monthly] = await Promise.all([
        api.get(`/api/parent/child/${childId}/today`),
        api.get(`/api/parent/child/${childId}/week`),
        api.get(`/api/parent/child/${childId}/monthly-report`).catch(() => null),
      ]);
      setToday(t);
      setWeek(w);
      if (monthly) setMonthlyReport(monthly);
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

  const exportCSV = () => {
    if (!selectedChild) return;
    const token = localStorage.getItem('token');
    const url = `${API_URL}/api/parent/child/${selectedChild}/export-csv`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `progreso_${child?.first_name || 'estudiante'}.csv`;
        a.click();
      });
  };

  const child = children.find(c => c.id === selectedChild);

  if (loading && !today) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div></div>;

  return (
    <div>
      {/* Child selector */}
      {children.length > 1 && (
        <div className="flex gap-2 mb-6">
          {children.map(c => (
            <button key={c.id} onClick={() => switchChild(c.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition ${
                selectedChild === c.id ? 'bg-amber-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}>
              <span>{c.avatar_url || '&#x1F9D2;'}</span>
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
            <p className="text-amber-100 mt-1">{child?.classroom_name || 'ThriveEd Panama'}</p>
          </div>
          <div className="flex items-center gap-4">
            {monthlyReport?.student && (
              <div className="text-center">
                <div className="flex items-center gap-1 justify-center">
                  <Trophy size={16} className="text-yellow-200" />
                  <span className="text-xl font-bold">Nv.{monthlyReport.student.level}</span>
                </div>
                <p className="text-xs text-amber-200">{monthlyReport.student.title}</p>
              </div>
            )}
            <div className="text-center">
              <div className="flex items-center gap-1">
                <Star size={16} className="text-yellow-200" />
                <span className="text-xl font-bold">{monthlyReport?.student?.streak_days || today?.streak_days || 0}</span>
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

      {/* View Toggle + Export */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          <button onClick={() => setShowMonthly(false)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              !showMonthly ? 'bg-amber-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}>
            Vista Diaria
          </button>
          <button onClick={() => setShowMonthly(true)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              showMonthly ? 'bg-amber-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
            }`}>
            <BarChart3 size={14} /> Reporte Mensual
          </button>
        </div>
        <button onClick={exportCSV}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
          <Download size={14} /> Exportar CSV
        </button>
      </div>

      {/* MONTHLY REPORT VIEW */}
      {showMonthly && monthlyReport ? (
        <div className="space-y-6">
          {/* Goals Progress Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <h3 className="text-sm text-gray-500 mb-2">Sesiones Completadas</h3>
              <div className="flex items-end justify-between">
                <span className="text-3xl font-bold text-gray-900">{monthlyReport.goals.sessions_completed}</span>
                <span className="text-sm text-gray-400">/ {monthlyReport.goals.sessions_target}</span>
              </div>
              <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
                <div className="h-full bg-green-500 rounded-full" style={{ width: `${monthlyReport.goals.sessions_progress}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">{monthlyReport.goals.sessions_progress}% de la meta</p>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <h3 className="text-sm text-gray-500 mb-2">Precision General</h3>
              <div className="flex items-end justify-between">
                <span className={`text-3xl font-bold ${monthlyReport.goals.accuracy_on_track ? 'text-green-600' : 'text-amber-600'}`}>
                  {monthlyReport.goals.accuracy_current}%
                </span>
                <span className="text-sm text-gray-400">meta: {monthlyReport.goals.accuracy_target}%</span>
              </div>
              <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
                <div className={`h-full rounded-full ${monthlyReport.goals.accuracy_on_track ? 'bg-green-500' : 'bg-amber-500'}`}
                  style={{ width: `${Math.min(100, monthlyReport.goals.accuracy_current)}%` }} />
              </div>
              <p className="text-xs mt-1">
                {monthlyReport.goals.accuracy_on_track
                  ? <span className="text-green-600">En camino</span>
                  : <span className="text-amber-600">Necesita mejorar</span>}
              </p>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
              <h3 className="text-sm text-gray-500 mb-2">Skills Dominados</h3>
              <div className="flex items-end justify-between">
                <span className="text-3xl font-bold text-purple-600">{monthlyReport.goals.mastery_current}</span>
                <span className="text-sm text-gray-400">/ {monthlyReport.goals.mastery_target}</span>
              </div>
              <div className="mt-2 w-full bg-gray-100 rounded-full h-2">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: `${monthlyReport.goals.mastery_progress}%` }} />
              </div>
              <p className="text-xs text-gray-500 mt-1">{monthlyReport.goals.mastery_progress}% del total</p>
            </div>
          </div>

          {/* Monthly Summary Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{monthlyReport.monthly_summary.days_active}</p>
              <p className="text-xs text-gray-500">Dias activos</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{monthlyReport.monthly_summary.completed_sessions}</p>
              <p className="text-xs text-gray-500">Sesiones completas</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{monthlyReport.monthly_summary.perfect_sessions}</p>
              <p className="text-xs text-gray-500">Sesiones perfectas</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm text-center">
              <p className="text-2xl font-bold text-gray-900">{monthlyReport.monthly_summary.total_time_minutes}</p>
              <p className="text-xs text-gray-500">Minutos totales</p>
            </div>
          </div>

          {/* Daily Activity Chart */}
          {monthlyReport.daily_chart && monthlyReport.daily_chart.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 size={18} /> Actividad Diaria (30 dias)
              </h2>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={monthlyReport.daily_chart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="session_date" tick={{ fontSize: 10 }} tickFormatter={(v: string) => v.slice(5)} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="total_correct" fill="#22c55e" name="Correctas" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="total_questions" fill="#e5e7eb" name="Total" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Weekly Trend */}
          {monthlyReport.weekly_chart && monthlyReport.weekly_chart.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp size={18} /> Tendencia Semanal
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={monthlyReport.weekly_chart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="week_start" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="total_correct" stroke="#8b5cf6" strokeWidth={2} name="Correctas" dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="completed" stroke="#22c55e" strokeWidth={2} name="Completadas" dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Category Mastery Radar */}
          {monthlyReport.categories && monthlyReport.categories.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Target size={18} /> Dominio por Categoria
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={monthlyReport.categories.map((c: any) => ({ ...c, subject: c.category }))}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Radar name="Dominio" dataKey="avg_mastery" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Skills Detail Table */}
          {monthlyReport.skills_mastery && monthlyReport.skills_mastery.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
              <h2 className="font-semibold text-gray-900 mb-4">Detalle de Skills</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-2 text-gray-500 font-medium">Skill</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Categoria</th>
                      <th className="text-center py-2 text-gray-500 font-medium">Dominio</th>
                      <th className="text-center py-2 text-gray-500 font-medium">Intentos</th>
                      <th className="text-center py-2 text-gray-500 font-medium">Correctas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyReport.skills_mastery.map((s: any, i: number) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 font-medium text-gray-900">{s.name}</td>
                        <td className="py-2 text-gray-500">{s.category}</td>
                        <td className="py-2 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-16 bg-gray-100 rounded-full h-2">
                              <div className={`h-full rounded-full ${
                                (s.mastery_level || 0) >= 0.9 ? 'bg-green-500' :
                                (s.mastery_level || 0) >= 0.5 ? 'bg-amber-500' : 'bg-red-400'
                              }`} style={{ width: `${(s.mastery_level || 0) * 100}%` }} />
                            </div>
                            <span className="text-xs">{((s.mastery_level || 0) * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="py-2 text-center text-gray-600">{s.attempts_count || 0}</td>
                        <td className="py-2 text-center text-gray-600">{s.correct_count || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* DAILY VIEW (Original) */
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
                      <p className="text-2xl font-bold text-purple-600">{today.session.skill_name || '---'}</p>
                      <p className="text-sm text-gray-500">Skill actual</p>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-500">Progreso de la mision</span>
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
                  <p>No hay actividad hoy aun</p>
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
            {/* Level Progress (new) */}
            {monthlyReport?.student && (
              <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Trophy size={16} className="text-amber-500" /> Nivel
                </h3>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-2xl">
                    {monthlyReport.student.icon}
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Nivel {monthlyReport.student.level}</p>
                    <p className="font-bold text-gray-900">{monthlyReport.student.title}</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                    style={{ width: `${monthlyReport.student.progress_percent}%` }} />
                </div>
                <p className="text-xs text-gray-500 mt-1">{monthlyReport.student.total_xp} XP total</p>
              </div>
            )}

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
                <TrendingUp size={16} /> Estadisticas
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Skills dominados</span>
                  <span className="font-medium">{monthlyReport?.monthly_summary?.skills_mastered || week?.skills_mastered || 0}/{monthlyReport?.monthly_summary?.total_skills || 32}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Sesiones completadas</span>
                  <span className="font-medium">{monthlyReport?.monthly_summary?.completed_sessions || week?.total_sessions || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Tiempo total</span>
                  <span className="font-medium">{monthlyReport?.monthly_summary?.total_time_minutes || week?.total_minutes || 0} min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Racha actual</span>
                  <span className="font-medium">{monthlyReport?.student?.streak_days || 0} dias</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
