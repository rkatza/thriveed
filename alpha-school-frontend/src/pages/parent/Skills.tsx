import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Map, CheckCircle, Circle } from 'lucide-react';

const CATEGORY_LABELS: Record<string, string> = {
  numeros: 'Números y Valor Posicional',
  operaciones: 'Suma y Resta',
  multiplicacion: 'Multiplicación',
  division: 'División',
  fracciones: 'Fracciones',
  geometria: 'Geometría',
  problemas: 'Resolución de Problemas',
};

export default function ParentSkills() {
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/parent/children').then(data => {
      setChildren(data);
      if (data.length > 0) {
        setSelectedChild(data[0].id);
        loadSkills(data[0].id);
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, []);

  const loadSkills = async (childId: number) => {
    setLoading(true);
    try {
      const data = await api.get(`/api/parent/child/${childId}/skill-map`);
      setSkills(data);
    } catch {} finally {
      setLoading(false);
    }
  };

  const switchChild = (childId: number) => {
    setSelectedChild(childId);
    loadSkills(childId);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div></div>;

  const categories = [...new Set(skills.map(s => s.category))];
  const child = children.find(c => c.id === selectedChild);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-3">
        <div className="flex items-center gap-3">
          <Map size={24} className="text-amber-600" />
          <h1 className="text-2xl font-bold text-gray-900">Mapa de Skills de {child?.first_name || ''}</h1>
        </div>
        {children.length > 1 && (
          <div className="flex gap-2">
            {children.map(c => (
              <button key={c.id} onClick={() => switchChild(c.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  selectedChild === c.id ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-700'
                }`}>
                {c.first_name}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-6">
        {categories.map(cat => {
          const catSkills = skills.filter(s => s.category === cat);
          const mastered = catSkills.filter(s => s.mastery_level >= 0.9).length;

          return (
            <div key={cat} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">{CATEGORY_LABELS[cat] || cat}</h2>
                <span className="text-sm text-gray-500">{mastered}/{catSkills.length} dominados</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {catSkills.map(skill => {
                  const mastery = skill.mastery_level || 0;
                  const isMastered = mastery >= 0.9;
                  return (
                    <div key={skill.skill_id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
                      {isMastered ? <CheckCircle size={18} className="text-green-500 shrink-0" /> : <Circle size={18} className="text-gray-300 shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{skill.skill_name}</p>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                          <div className={`h-full rounded-full ${isMastered ? 'bg-green-500' : mastery > 0 ? 'bg-amber-400' : 'bg-gray-200'}`}
                            style={{ width: `${mastery * 100}%` }} />
                        </div>
                      </div>
                      <span className="text-xs text-gray-500 shrink-0">{(mastery * 100).toFixed(0)}%</span>
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
