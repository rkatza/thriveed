import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { MessageSquare, Send } from 'lucide-react';

export default function CoachMessages() {
  const [parents, setParents] = useState<any[]>([]);
  const [selectedParent, setSelectedParent] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sentMessages, setSentMessages] = useState<any[]>([]);

  useEffect(() => {
    // Load parents from students' parents
    api.get('/api/coach/classroom/live').then(data => {
      const parentList = (data.students || []).map((s: any) => ({
        student_id: s.student_id,
        name: `${s.first_name} ${s.last_name}`,
        avatar: s.avatar_url || '🧒',
      }));
      setParents(parentList);
      if (parentList.length > 0) setSelectedParent(parentList[0].student_id);
    }).finally(() => setLoading(false));
  }, []);

  const sendMessage = async () => {
    if (!message.trim() || !selectedParent) return;
    setSending(true);
    try {
      await api.post('/api/coach/message', {
        parent_user_id: selectedParent,
        student_id: selectedParent,
        subject: 'Mensaje del coach',
        body: message,
      });
      setSentMessages(prev => [...prev, {
        student_id: selectedParent,
        message,
        sent_at: new Date().toISOString(),
      }]);
      setMessage('');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mensajes a Padres</h1>

      <div className="grid grid-cols-3 gap-6">
        {/* Student selector */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 text-sm">Estudiantes</h2>
          </div>
          <div className="divide-y divide-gray-50">
            {parents.map(p => (
              <button key={p.student_id} onClick={() => setSelectedParent(p.student_id)}
                className={`w-full flex items-center gap-3 p-4 text-left transition ${
                  selectedParent === p.student_id ? 'bg-teal-50' : 'hover:bg-gray-50'
                }`}>
                <span className="text-xl">{p.avatar}</span>
                <span className={`text-sm font-medium ${selectedParent === p.student_id ? 'text-teal-700' : 'text-gray-700'}`}>
                  {p.name}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Message area */}
        <div className="col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm flex flex-col">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <MessageSquare size={18} />
              Mensaje al padre/madre de {parents.find(p => p.student_id === selectedParent)?.name || '...'}
            </h2>
          </div>

          {/* Sent messages */}
          <div className="flex-1 p-4 space-y-3 min-h-64">
            {sentMessages.filter(m => m.student_id === selectedParent).map((m, i) => (
              <div key={i} className="ml-auto max-w-xs bg-teal-600 text-white p-3 rounded-2xl rounded-br-sm">
                <p className="text-sm">{m.message}</p>
                <p className="text-xs text-teal-200 mt-1">{new Date(m.sent_at).toLocaleTimeString('es-PA')}</p>
              </div>
            ))}
            {sentMessages.filter(m => m.student_id === selectedParent).length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                Envía un mensaje al padre/madre del estudiante
              </div>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-100">
            <div className="flex gap-2">
              <input value={message} onChange={e => setMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Escribe un mensaje..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-teal-500 outline-none" />
              <button onClick={sendMessage} disabled={sending || !message.trim()}
                className="px-4 py-3 bg-teal-600 text-white rounded-xl hover:bg-teal-700 transition disabled:opacity-50">
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
