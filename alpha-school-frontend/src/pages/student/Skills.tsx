import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Map, Lock, CheckCircle, Circle } from 'lucide-react';

const CATEGORY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  numeros: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  operaciones: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  multiplicacion: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  division: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  fracciones: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700' },
  geometria: { bg: 'bg-teal-50', border: 'border-teal-200', text: 'text-teal-700' },
  problemas: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
};

const CATEGORY_LABELS: Record<string, string> = {
  numeros: 'Números y Valor Posicional',
  operaciones: 'Suma y Resta',
  multiplicacion: 'Multiplicación',
  division: 'División',
  fracciones: 'Fracciones',
  geometria: 'Geometría',
  problemas: 'Resolución de Problemas',
};

export default function StudentSkills() {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/student/skill-map').then(setSkills).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  const categories = [...new Set(skills.map(s => s.category))];

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Map size={24} className="text-indigo-600" />
        <h1 className="text-2xl font-bold text-gray-900">Mapa de Skills</h1>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {categories.map(cat => {
          const catSkills = skills.filter(s => s.category === cat);
          const colors = CATEGORY_COLORS[cat] || { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700' };
          const mastered = catSkills.filter(s => s.mastery_level >= 0.9).length;

          return (
            <div key={cat} className={`rounded-xl border ${colors.border} ${colors.bg} p-5`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className={`font-semibold ${colors.text}`}>{CATEGORY_LABELS[cat] || cat}</h2>
                <span className={`text-xs font-medium ${colors.text} px-2 py-0.5 rounded-full border ${colors.border}`}>
                  {mastered}/{catSkills.length}
                </span>
              </div>
              <div className="space-y-2">
                {catSkills.map(skill => {
                  const mastery = skill.mastery_level || 0;
                  const isMastered = mastery >= 0.9;
                  const isInProgress = mastery > 0 && mastery < 0.9;
                  const isLocked = !skill.unlocked;

                  return (
                    <div key={skill.skill_id} className={`flex items-center gap-3 p-3 rounded-lg bg-white/70 ${isLocked ? 'opacity-50' : ''}`}>
                      <div className="shrink-0">
                        {isMastered ? (
                          <CheckCircle size={20} className="text-green-500" />
                        ) : isLocked ? (
                          <Lock size={20} className="text-gray-400" />
                        ) : (
                          <Circle size={20} className={isInProgress ? 'text-amber-400' : 'text-gray-300'} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{skill.skill_name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div className={`h-full rounded-full ${isMastered ? 'bg-green-500' : isInProgress ? 'bg-amber-400' : 'bg-gray-200'}`}
                              style={{ width: `${mastery * 100}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{(mastery * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
