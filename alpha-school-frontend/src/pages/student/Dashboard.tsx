import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { Rocket, Star, Trophy, BookOpen, Target, HelpCircle, Loader2, CheckCircle, XCircle } from 'lucide-react';

export default function StudentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [mission, setMission] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [exercise, setExercise] = useState<any>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [answering, setAnswering] = useState(false);
  const [helpSent, setHelpSent] = useState(false);
  const [numericAnswer, setNumericAnswer] = useState('');

  useEffect(() => {
    // Check if placement test is needed
    if (user && !user.placement_test_completed) {
      navigate('/student/placement-test');
      return;
    }
    loadData();
  }, [user]);

  const loadData = async () => {
    try {
      const [m, p] = await Promise.all([
        api.get('/api/student/daily-mission'),
        api.get('/api/student/profile'),
      ]);
      setMission(m);
      setProfile(p);
      const qs = m.questions || m.exercises || [];
      if (qs.length > 0) {
        // Filter out already-answered questions
        const unanswered = qs.filter((q: any) => !(m.answered_ids || []).includes(q.id));
        if (unanswered.length > 0) {
          setExercise(unanswered[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!selectedAnswer || !exercise) return;
    setAnswering(true);
    try {
      const result = await api.post('/api/student/exercise/answer', {
        session_id: mission.session?.id || mission.session_id,
        question_id: exercise.id,
        answer: selectedAnswer,
        time_spent_seconds: 30,
      });
      setFeedback(result);

      setTimeout(() => {
        // Move to next exercise
        const qs = mission.questions || mission.exercises || [];
        if (qs.length > 0) {
          const currentIdx = qs.findIndex((e: any) => e.id === exercise.id);
          if (currentIdx < qs.length - 1) {
            setExercise(qs[currentIdx + 1]);
            setSelectedAnswer(null);
            setNumericAnswer('');
            setFeedback(null);
          } else if (result.session_complete) {
            // Mission complete - reload
            loadData();
          } else {
            // More questions needed - reload
            loadData();
          }
        }
        setAnswering(false);
      }, 2000);
    } catch {
      setAnswering(false);
    }
  };

  const sendHelpRequest = async () => {
    try {
      await api.post('/api/student/help-request', {
        question_id: exercise?.id,
        message: '¡Necesito ayuda con este ejercicio!',
      });
      setHelpSent(true);
      setTimeout(() => setHelpSent(false), 3000);
    } catch {}
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  const sessionData = mission?.session || mission || {};
  const totalQuestions = mission?.total_questions || sessionData?.total_questions || 0;
  const answeredCount = mission?.answered_ids?.length || sessionData?.total_questions || 0;
  const missionProgress = mission?.progress || { completed: answeredCount, total: totalQuestions };
  const progressPercent = missionProgress.total > 0 ? (missionProgress.completed / missionProgress.total) * 100 : 0;

  return (
    <div>
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">¡Hola {user?.first_name}! 🚀</h1>
            <p className="text-indigo-100 mt-1">
              {mission?.session?.mission_title || mission?.mission_title || 'Tu misión de hoy te espera'}
            </p>
            {profile?.curriculum_level && (
              <span className="inline-block mt-2 px-3 py-1 bg-white/20 rounded-full text-xs font-medium">
                {profile.curriculum_level === 'kinder' ? '🧒 Módulo Kinder' : '📚 Módulo 4to Grado'}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className="flex items-center gap-1">
                <Star size={16} className="text-amber-300" />
                <span className="text-xl font-bold">{profile?.streak_days || 0}</span>
              </div>
              <p className="text-xs text-indigo-200">Racha</p>
            </div>
            <div className="text-center">
              <div className="flex items-center gap-1">
                <Trophy size={16} className="text-amber-300" />
                <span className="text-xl font-bold">{profile?.total_xp || 0}</span>
              </div>
              <p className="text-xs text-indigo-200">XP</p>
            </div>
          </div>
        </div>

        {/* Mission progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progreso de la misión</span>
            <span>{missionProgress.completed}/{missionProgress.total} ejercicios</span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-3">
            <div className="h-full bg-white rounded-full transition-all duration-500" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Main exercise area */}
        <div className="col-span-2">
          {exercise ? (
            <div className="bg-white rounded-2xl p-8 border border-gray-100 shadow-sm">
              {/* Exercise header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                    {exercise.skill_name || mission?.skill_name || 'Matemáticas'}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                    Nivel {exercise.difficulty_level || 1}
                  </span>
                </div>
                <button onClick={sendHelpRequest} disabled={helpSent}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition ${helpSent ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-700 hover:bg-amber-200'}`}>
                  {helpSent ? <><CheckCircle size={14} /> Ayuda enviada</> : <><HelpCircle size={14} /> Pedir ayuda</>}
                </button>
              </div>

              {/* Question */}
              <h2 className="text-xl font-semibold text-gray-900 mb-6">{exercise.question_text}</h2>

              {/* Options or numeric input */}
              {(() => {
                const opts = Array.isArray(exercise.options) ? exercise.options : JSON.parse(exercise.options || '[]');
                const isNumeric = exercise.question_type === 'numeric' || opts.length === 0;
                
                if (isNumeric) {
                  return (
                    <div className="mb-6">
                      <div className="flex gap-3">
                        <input
                          type="text"
                          inputMode="numeric"
                          value={numericAnswer}
                          onChange={(e) => {
                            setNumericAnswer(e.target.value);
                            setSelectedAnswer(e.target.value);
                          }}
                          disabled={!!feedback}
                          placeholder="Escribe tu respuesta..."
                          className={`flex-1 p-4 rounded-xl border-2 text-lg font-medium transition
                            ${feedback ? (feedback.is_correct ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50') :
                              'border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200'}`}
                          onKeyDown={(e) => { if (e.key === 'Enter' && selectedAnswer && !feedback) submitAnswer(); }}
                        />
                      </div>
                      {feedback && !feedback.is_correct && (
                        <p className="mt-2 text-sm text-gray-500">Respuesta correcta: <span className="font-semibold text-green-600">{feedback.correct_answer}</span></p>
                      )}
                    </div>
                  );
                }
                
                return (
                  <div className="grid grid-cols-1 gap-3 mb-6">
                    {opts.map((opt: string, idx: number) => {
                      const isSelected = selectedAnswer === opt;
                      const showFeedback = feedback !== null;
                      const isCorrectOption = showFeedback && opt === (feedback.correct_answer || exercise.correct_answer);
                      const isWrongSelected = showFeedback && isSelected && !feedback.is_correct;

                      return (
                        <button key={idx}
                          onClick={() => !feedback && setSelectedAnswer(opt)}
                          disabled={!!feedback}
                          className={`p-4 rounded-xl border-2 text-left transition font-medium text-lg
                            ${isCorrectOption ? 'border-green-500 bg-green-50 text-green-700' :
                              isWrongSelected ? 'border-red-500 bg-red-50 text-red-700' :
                              isSelected ? 'border-indigo-500 bg-indigo-50 text-indigo-700' :
                              'border-gray-200 hover:border-gray-300 text-gray-700'}`}>
                          <div className="flex items-center justify-between">
                            <span>{opt}</span>
                            {isCorrectOption && <CheckCircle size={20} className="text-green-500" />}
                            {isWrongSelected && <XCircle size={20} className="text-red-500" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                );
              })()}

              {/* Feedback */}
              {feedback && (
                <div className={`p-4 rounded-xl mb-4 ${feedback.is_correct ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                  <p className="font-semibold text-lg">
                    {feedback.is_correct ? '¡Excelente! 🌟' : '¡Casi! 💪'}
                  </p>
                  {feedback.explanation && <p className="text-sm mt-1">{feedback.explanation}</p>}
                  {feedback.xp_earned > 0 && <p className="text-sm mt-1">+{feedback.xp_earned} XP</p>}
                </div>
              )}

              {/* Submit button */}
              {!feedback && (
                <button onClick={submitAnswer} disabled={!selectedAnswer || answering}
                  className="w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 transition disabled:opacity-50">
                  {answering ? <Loader2 className="animate-spin mx-auto" /> : 'Confirmar Respuesta'}
                </button>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-12 text-center border border-gray-100 shadow-sm">
              <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Trophy className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">¡Misión Completada! 🎉</h2>
              <p className="text-gray-500 mb-6">Has completado todos los ejercicios de hoy. ¡Vuelve mañana para tu próxima misión!</p>
              <div className="flex justify-center gap-4">
                <button onClick={() => navigate('/student/progress')}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition">
                  Ver mi progreso
                </button>
                <button onClick={() => navigate('/student/achievements')}
                  className="px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition">
                  Mis logros
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Today's stats */}
          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Rocket size={16} /> Hoy
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Ejercicios</span>
                <span className="font-semibold text-gray-900">{missionProgress.completed}/{missionProgress.total}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Skill actual</span>
                <span className="text-sm font-medium text-indigo-600">{mission?.session?.skill_name || mission?.skill_name || '—'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Estado</span>
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                  (mission?.session?.status || mission?.status) === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {(mission?.session?.status || mission?.status) === 'completed' ? 'Completada' : 'En progreso'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3">Accesos rápidos</h3>
            <div className="space-y-2">
              <button onClick={() => navigate('/student/progress')}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition text-left">
                <Target size={18} className="text-purple-500" />
                <span className="text-sm text-gray-700">Mi progreso</span>
              </button>
              <button onClick={() => navigate('/student/skills')}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition text-left">
                <BookOpen size={18} className="text-blue-500" />
                <span className="text-sm text-gray-700">Mapa de skills</span>
              </button>
              <button onClick={() => navigate('/student/achievements')}
                className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition text-left">
                <Trophy size={18} className="text-amber-500" />
                <span className="text-sm text-gray-700">Mis logros</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
