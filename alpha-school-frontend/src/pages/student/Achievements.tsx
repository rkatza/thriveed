import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Trophy } from 'lucide-react';

export default function StudentAchievements() {
  const [achievements, setAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/student/achievements').then(setAchievements).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Trophy size={24} className="text-amber-500" />
        <h1 className="text-2xl font-bold text-gray-900">Mis Logros</h1>
      </div>

      {achievements.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-gray-100 shadow-sm">
          <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-8 h-8 text-amber-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">¡Aún no tienes logros!</h2>
          <p className="text-gray-500">Completa ejercicios y misiones para ganar tus primeros logros. 🌟</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {achievements.map(a => (
            <div key={a.id} className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition text-center">
              <span className="text-5xl block mb-3">{a.icon}</span>
              <h3 className="font-semibold text-gray-900 mb-1">{a.title}</h3>
              <p className="text-sm text-gray-500 mb-2">{a.description}</p>
              <span className="text-xs text-gray-400">
                {new Date(a.earned_at).toLocaleDateString('es-PA')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
