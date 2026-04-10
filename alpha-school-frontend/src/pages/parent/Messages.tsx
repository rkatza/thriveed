import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { MessageSquare, Send } from 'lucide-react';

export default function ParentMessages() {
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [coachId, setCoachId] = useState<number | null>(null);
  const [studentId, setStudentId] = useState<number | null>(null);

  useEffect(() => {
    // Load messages and find the coach/student for sending
    Promise.all([
      api.get('/api/parent/messages'),
      api.get('/api/parent/children'),
    ]).then(([msgs, children]) => {
      setMessages(msgs);
      if (children.length > 0) {
        setStudentId(children[0].id);
        // Try to find coach from the child's classroom
        if (children[0].classroom_id) {
          // Look for coach in received messages, or use a default
          const coachMsg = msgs.find((m: any) => m.sender_id !== undefined && m.receiver_first);
          if (coachMsg) {
            setCoachId(coachMsg.sender_id);
          }
        }
      }
    }).finally(() => setLoading(false));
  }, []);

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await api.post('/api/parent/messages', {
        receiver_id: coachId || 1,
        student_id: studentId || 1,
        subject: 'Mensaje del padre',
        body: newMessage,
      });
      // Reload messages to get the full data
      const msgs = await api.get('/api/parent/messages');
      setMessages(msgs);
      setNewMessage('');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
        <MessageSquare size={24} className="text-amber-600" />
        Mensajes con el Coach
      </h1>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm flex flex-col" style={{ minHeight: '500px' }}>
        {/* Messages list */}
        <div className="flex-1 p-6 space-y-4 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              No hay mensajes aún. Envíe un mensaje al coach de su hijo/a.
            </div>
          ) : (
            messages.map(m => (
              <div key={m.id} className={`flex ${m.sender_role === 'parent' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-md p-4 rounded-2xl ${
                  m.sender_role === 'parent'
                    ? 'bg-amber-600 text-white rounded-br-sm'
                    : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                }`}>
                  <p className="text-sm">{m.message}</p>
                  <p className={`text-xs mt-1 ${m.sender_role === 'parent' ? 'text-amber-200' : 'text-gray-400'}`}>
                    {m.sender_name && <span className="font-medium">{m.sender_name} · </span>}
                    {new Date(m.created_at).toLocaleString('es-PA')}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex gap-2">
            <input value={newMessage} onChange={e => setNewMessage(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Escriba un mensaje al coach..."
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 outline-none" />
            <button onClick={sendMessage} disabled={sending || !newMessage.trim()}
              className="px-4 py-3 bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition disabled:opacity-50">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
