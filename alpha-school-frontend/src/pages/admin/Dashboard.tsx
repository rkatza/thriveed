import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Users, BookOpen, Clock, Target, AlertTriangle, GraduationCap, Download } from 'lucide-react';

export default function AdminDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/admin/dashboard').then(setData).finally(() => setLoading(false));
  }, []);

  const exportStudents = async () => {
    const blob = await api.get('/api/admin/export/students');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'estudiantes.csv'; a.click();
  };

  const exportMastery = async () => {
    const blob = await api.get('/api/admin/export/mastery');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'mastery.csv'; a.click();
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return null;

  const kpis = [
    { label: 'Estudiantes', value: data.total_students, icon: <Users size={24} />, color: 'bg-blue-500' },
    { label: 'Sesiones Hoy', value: `${data.completed_sessions_today}/${data.active_sessions_today}`, icon: <BookOpen size={24} />, color: 'bg-green-500' },
    { label: 'Tiempo Promedio', value: `${data.avg_session_time_minutes} min`, icon: <Clock size={24} />, color: 'bg-amber-500' },
    { label: 'Tasa de Mastery', value: `${data.avg_mastery_rate}%`, icon: <Target size={24} />, color: 'bg-purple-500' },
    { label: 'Alertas', value: data.pending_alerts, icon: <AlertTriangle size={24} />, color: 'bg-red-500' },
    { label: 'Placement Tests', value: `${data.placement_tests_completed}/${data.total_students}`, icon: <GraduationCap size={24} />, color: 'bg-teal-500' },
    { label: 'Coaches', value: data.total_coaches, icon: <Users size={24} />, color: 'bg-indigo-500' },
    { label: 'Padres', value: data.total_parents, icon: <Users size={24} />, color: 'bg-pink-500' },
  ];

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Panel de Administración</h1>
          <p className="text-gray-500">Piloto ThriveEd Panamá · Matemáticas</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportStudents} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-white border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-gray-50 transition">
            <Download size={16} /> <span className="hidden sm:inline">Exportar</span> Estudiantes
          </button>
          <button onClick={exportMastery} className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-white border border-gray-200 rounded-lg text-xs sm:text-sm hover:bg-gray-50 transition">
            <Download size={16} /> <span className="hidden sm:inline">Exportar</span> Mastery
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {kpis.map(kpi => (
          <div key={kpi.label} className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 ${kpi.color} rounded-lg flex items-center justify-center text-white`}>
                {kpi.icon}
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
            <p className="text-sm text-gray-500">{kpi.label}</p>
          </div>
        ))}
      </div>

      {/* Recent sessions */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Sesiones Recientes</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estudiante</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Skill</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Correctas</th>
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Tiempo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.recent_sessions.map((s: any) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 text-sm font-medium text-gray-900">{s.first_name} {s.last_name}</td>
                  <td className="px-5 py-3 text-sm text-gray-600">{s.skill_name}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-1 text-xs rounded-full font-medium
                      ${s.status === 'completed' ? 'bg-green-100 text-green-700' :
                        s.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'}`}>
                      {s.status === 'completed' ? 'Completada' : s.status === 'in_progress' ? 'En progreso' : s.status}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600">{s.correct_answers}/{s.total_questions}</td>
                  <td className="px-5 py-3 text-sm text-gray-600">{Math.round(s.active_time_seconds / 60)} min</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
