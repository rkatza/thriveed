import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { BookOpen, Eye, EyeOff } from 'lucide-react';

const CATEGORY_LABELS: Record<string, string> = {
  numeros: 'Números y Valor Posicional',
  operaciones: 'Suma y Resta',
  multiplicacion: 'Multiplicación',
  division: 'División',
  fracciones: 'Fracciones',
  geometria: 'Geometría',
  problemas: 'Resolución de Problemas',
};

const CATEGORY_COLORS: Record<string, string> = {
  numeros: 'bg-blue-100 text-blue-700',
  operaciones: 'bg-green-100 text-green-700',
  multiplicacion: 'bg-purple-100 text-purple-700',
  division: 'bg-amber-100 text-amber-700',
  fracciones: 'bg-pink-100 text-pink-700',
  geometria: 'bg-teal-100 text-teal-700',
  problemas: 'bg-red-100 text-red-700',
};

export default function Curriculum() {
  const [skills, setSkills] = useState<any[]>([]);
  const [lessons, setLessons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get('/api/admin/skills'), api.get('/api/admin/lessons')])
      .then(([s, l]) => { setSkills(s); setLessons(l); })
      .finally(() => setLoading(false));
  }, []);

  const toggleLesson = async (id: number) => {
    const result = await api.put(`/api/admin/lessons/${id}/publish`);
    setLessons(lessons.map(l => l.id === id ? { ...l, is_published: result.is_published ? 1 : 0 } : l));
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  const categories = [...new Set(skills.map(s => s.category))];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Currículo de 4to Grado - Matemáticas</h1>
      <div className="space-y-6">
        {categories.map(cat => (
          <div key={cat} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center gap-3">
              <BookOpen size={18} className="text-gray-400" />
              <h2 className="font-semibold text-gray-900">{CATEGORY_LABELS[cat] || cat}</h2>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLORS[cat]}`}>
                {skills.filter(s => s.category === cat).length} skills
              </span>
            </div>
            <div className="divide-y divide-gray-50">
              {skills.filter(s => s.category === cat).map(skill => {
                const lesson = lessons.find(l => l.skill_id === skill.id);
                return (
                  <div key={skill.id} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                        skill.difficulty_level <= 1 ? 'bg-green-100 text-green-700' :
                        skill.difficulty_level <= 2 ? 'bg-amber-100 text-amber-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        N{skill.difficulty_level}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{skill.name}</p>
                        <p className="text-xs text-gray-500">{skill.description}</p>
                      </div>
                    </div>
                    {lesson && (
                      <button onClick={() => toggleLesson(lesson.id)}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          lesson.is_published ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                        }`}>
                        {lesson.is_published ? <><Eye size={12} /> Publicado</> : <><EyeOff size={12} /> Despublicado</>}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
