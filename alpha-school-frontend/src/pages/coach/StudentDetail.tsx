import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { ArrowLeft, Target, BookOpen, MessageSquare, AlertTriangle } from 'lucide-react';

const INTERVENTION_TAGS = [
  { value: 'motivacional', label: 'Motivacional', color: 'bg-blue-100 text-blue-700' },
  { value: 'conceptual', label: 'Conceptual', color: 'bg-purple-100 text-purple-700' },
  { value: 'tecnico', label: 'Técnico', color: 'bg-amber-100 text-amber-700' },
  { value: 'comportamiento', label: 'Comportamiento', color: 'bg-red-100 text-red-700' },
];

export default function CoachStudentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [mastery, setMastery] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [interventionTag, setInterventionTag] = useState('motivacional');
  const [interventionNotes, setInterventionNotes] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get(`/api/coach/student/${id}/detail`),
      api.get(`/api/coach/student/${id}/mastery-map`),
    ]).then(([d, m]) => {
      // Normalize API response
      d.sessions = d.sessions || d.recent_attempts || [];
      d.interventions = d.interventions || [];
      setData(d);
      setMastery(Array.isArray(m) ? m : m.skills || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  const submitIntervention = async () => {
    if (!interventionNotes.trim()) return;
    setSending(true);
    try {
      await api.post('/api/coach/intervention', {
        student_id: Number(id),
        tag: interventionTag,
        notes: interventionNotes,
      });
      setInterventionNotes('');
      // Reload data
      const d = await api.get(`/api/coach/student/${id}/detail`);
      setData(d);
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  if (!data) return <p>Estudiante no encontrado</p>;

  const student = data.student || {};
  const sessions = data.sessions || data.recent_attempts || [];
  const interventions = data.interventions || [];

  return (
    <div>
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Volver al salón
      </button>

      {/* Header */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mb-6">
        <div className="flex items-center gap-4">
          <span className="text-4xl">{student.avatar_url || '🧒'}</span>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{student.first_name} {student.last_name}</h1>
            <p className="text-gray-500">{student.age} años · {student.nickname}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Mastery Map */}
        <div className="col-span-2 bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><Target size={18} /> Mapa de Mastery</h2>
          <div className="space-y-2">
            {mastery.map((m: any) => (
              <div key={m.skill_id} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-36 truncate">{m.skill_name}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div className={`h-full rounded-full ${m.mastery_level >= 0.9 ? 'bg-green-500' : m.mastery_level >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                    style={{ width: `${m.mastery_level * 100}%` }} />
                </div>
                <span className="text-xs font-medium w-12 text-right">{(m.mastery_level * 100).toFixed(0)}%</span>
              </div>
            ))}
            {mastery.length === 0 && <p className="text-sm text-gray-400">Sin datos de mastery aún</p>}
          </div>
        </div>

        {/* New intervention */}
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MessageSquare size={18} /> Nueva Intervención
          </h2>
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {INTERVENTION_TAGS.map(tag => (
                <button key={tag.value} onClick={() => setInterventionTag(tag.value)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                    interventionTag === tag.value ? tag.color + ' ring-2 ring-offset-1' : 'bg-gray-100 text-gray-600'
                  }`}>
                  {tag.label}
                </button>
              ))}
            </div>
            <textarea value={interventionNotes} onChange={e => setInterventionNotes(e.target.value)}
              placeholder="Notas de la intervención..."
              className="w-full p-3 border border-gray-200 rounded-lg text-sm resize-none h-24 focus:ring-2 focus:ring-teal-500 outline-none" />
            <button onClick={submitIntervention} disabled={sending || !interventionNotes.trim()}
              className="w-full py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 transition disabled:opacity-50">
              {sending ? 'Enviando...' : 'Registrar Intervención'}
            </button>
          </div>
        </div>
      </div>

      {/* Sessions */}
      <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mt-6">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><BookOpen size={18} /> Sesiones Recientes</h2>
        <div className="space-y-2">
          {sessions.map((s: any) => (
            <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">{s.mission_title}</p>
                <p className="text-xs text-gray-500">{s.session_date} · {s.skill_name}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">{s.correct_answers}/{s.total_questions}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${s.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                  {s.status === 'completed' ? 'Completada' : 'En progreso'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Past interventions */}
      {interventions.length > 0 && (
        <div className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm mt-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2"><AlertTriangle size={18} /> Historial de Intervenciones</h2>
          <div className="space-y-3">
            {interventions.map((i: any) => (
              <div key={i.id} className="p-3 bg-amber-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs font-medium">{i.tag}</span>
                  <span className="text-xs text-gray-500">{new Date(i.created_at).toLocaleString('es-PA')}</span>
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
