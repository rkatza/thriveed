import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { Brain, Star, Sparkles, CheckCircle, XCircle, ArrowRight, Loader2 } from 'lucide-react';
import KinderQuestionCard from '../../components/KinderQuestionCard';

const INTEREST_OPTIONS = [
  { id: 'deportes', label: 'Deportes', emoji: '⚽' },
  { id: 'cocina', label: 'Cocina', emoji: '🍳' },
  { id: 'arte', label: 'Arte', emoji: '🎨' },
  { id: 'dinosaurios', label: 'Dinosaurios', emoji: '🦕' },
  { id: 'carros', label: 'Carros', emoji: '🚗' },
  { id: 'animales', label: 'Animales', emoji: '🐾' },
  { id: 'musica', label: 'Música', emoji: '🎵' },
  { id: 'videojuegos', label: 'Videojuegos', emoji: '🎮' },
  { id: 'naturaleza', label: 'Naturaleza', emoji: '🌿' },
  { id: 'espacio', label: 'Espacio', emoji: '🚀' },
];

type Phase = 'welcome' | 'interests' | 'testing' | 'feedback' | 'results';

export default function PlacementTest() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>('welcome');
  const [interests, setInterests] = useState<string[]>([]);
  const [testData, setTestData] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [questionNum, setQuestionNum] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(20);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const toggleInterest = (id: string) => {
    setInterests(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  };

  const submitInterests = async () => {
    setLoading(true);
    try {
      await api.post('/api/student/interests', { interests });
      // Update local user
      const savedUser = JSON.parse(localStorage.getItem('user') || '{}');
      savedUser.interests = JSON.stringify(interests);
      localStorage.setItem('user', JSON.stringify(savedUser));
      startTest();
    } catch {
      startTest();
    }
  };

  const startTest = async () => {
    setLoading(true);
    try {
      const data = await api.get('/api/student/placement-test/start');
      setTestData(data);
      if (data.status === 'completed') {
        setResults(data);
        setPhase('results');
      } else {
        setCurrentQuestion(data.next_question || data.question);
        setQuestionNum((data.questions_answered || 0) + 1);
        setTotalQuestions(data.total_questions || 20);
        setPhase('testing');
      }
    } catch (err: any) {
      if (err.message?.includes('ya completada')) {
        const res = await api.get('/api/student/placement-test/results');
        setResults(res);
        setPhase('results');
      }
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!selectedAnswer || !testData) return;
    setLoading(true);
    try {
      const data = await api.post('/api/student/placement-test/answer', {
        test_id: testData.test_id,
        question_id: currentQuestion.id,
        answer: selectedAnswer,
      });
      setIsCorrect(data.is_correct);
      setPhase('feedback');

      setTimeout(async () => {
        if (data.next_question) {
          setCurrentQuestion(data.next_question);
          setQuestionNum(prev => prev + 1);
          setSelectedAnswer(null);
          setIsCorrect(null);
          setPhase('testing');
        } else {
          const res = await api.get('/api/student/placement-test/results');
          setResults(res);
          setPhase('results');
        }
        setLoading(false);
      }, 1500);
    } catch {
      setLoading(false);
    }
  };

  // Welcome screen
  if (phase === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-lg text-center">
          <div className="w-20 h-20 bg-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">¡Hola {user?.first_name}! 👋</h1>
          <p className="text-lg text-gray-600 mb-2">Bienvenido/a a ThriveEd</p>
          <p className="text-gray-500 mb-8">
            Vamos a hacer un test rápido para conocer tu nivel en matemáticas.
            No te preocupes, no es un examen — solo queremos saber por dónde empezar. 🎯
          </p>
          <div className="bg-white rounded-2xl p-6 mb-6 text-left shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-3">¿Cómo funciona?</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex gap-2"><Sparkles size={16} className="text-purple-500 mt-0.5 shrink-0" /> Las preguntas se adaptan a tu nivel</li>
              <li className="flex gap-2"><Star size={16} className="text-amber-500 mt-0.5 shrink-0" /> No hay respuestas incorrectas — todo ayuda a conocerte mejor</li>
              <li className="flex gap-2"><CheckCircle size={16} className="text-green-500 mt-0.5 shrink-0" /> Toma entre 15-25 minutos</li>
            </ul>
          </div>
          <button onClick={() => setPhase('interests')}
            className="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-semibold text-lg hover:bg-indigo-700 transition shadow-lg shadow-indigo-200">
            ¡Vamos! <ArrowRight className="inline ml-2" size={20} />
          </button>
        </div>
      </div>
    );
  }

  // Interest selection
  if (phase === 'interests') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">¿Qué te gusta? 🎯</h2>
          <p className="text-gray-500 text-center mb-6">Elige hasta 3 cosas que te gusten. Vamos a personalizar tus ejercicios.</p>
          <div className="grid grid-cols-2 gap-3 mb-8">
            {INTEREST_OPTIONS.map(opt => {
              const selected = interests.includes(opt.id);
              return (
                <button key={opt.id} onClick={() => toggleInterest(opt.id)}
                  className={`flex items-center gap-3 p-4 rounded-xl border-2 transition text-left
                    ${selected ? 'border-indigo-500 bg-indigo-50 shadow-md' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
                  <span className="text-3xl">{opt.emoji}</span>
                  <span className={`font-medium ${selected ? 'text-indigo-700' : 'text-gray-700'}`}>{opt.label}</span>
                </button>
              );
            })}
          </div>
          <button onClick={submitInterests} disabled={interests.length === 0 || loading}
            className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-semibold text-lg hover:bg-indigo-700 transition disabled:opacity-50">
            {loading ? <Loader2 className="animate-spin mx-auto" /> : `Continuar (${interests.length}/3 seleccionados)`}
          </button>
        </div>
      </div>
    );
  }

  // Direct submit helper for kinder (auto-submit on option tap)
  const submitAnswerDirect = async (answer: string) => {
    if (!testData) return;
    setLoading(true);
    try {
      const data = await api.post('/api/student/placement-test/answer', {
        test_id: testData.test_id,
        question_id: currentQuestion.id,
        answer,
      });
      setIsCorrect(data.is_correct);
      setPhase('feedback');

      setTimeout(async () => {
        if (data.next_question) {
          setCurrentQuestion(data.next_question);
          setQuestionNum(prev => prev + 1);
          setSelectedAnswer(null);
          setIsCorrect(null);
          setPhase('testing');
        } else {
          const res = await api.get('/api/student/placement-test/results');
          setResults(res);
          setPhase('results');
        }
        setLoading(false);
      }, 1500);
    } catch {
      setLoading(false);
    }
  };

  // Detect kinder student
  const isKinder = user?.curriculum_level === 'kinder';

  // Testing phase
  if (phase === 'testing' || phase === 'feedback') {
    const rawOptions = currentQuestion?.options || '[]';
    const options: string[] = Array.isArray(rawOptions) ? rawOptions : JSON.parse(rawOptions);
    const isNumeric = options.length === 0;
    const progress = (questionNum / totalQuestions) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full">
          {/* Progress bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm text-gray-500 mb-2">
              <span>Pregunta {questionNum} de {totalQuestions}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-white rounded-full h-3 overflow-hidden shadow-inner">
              <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }} />
            </div>
          </div>

          {/* Question card — Kinder visual mode vs standard text mode */}
          {isKinder && currentQuestion?.options_media ? (
            <KinderQuestionCard
              question={currentQuestion}
              onAnswer={(answer) => {
                setSelectedAnswer(answer);
                submitAnswerDirect(answer);
              }}
              feedback={
                phase === 'feedback'
                  ? {
                      is_correct: isCorrect ?? false,
                      correct_answer: currentQuestion?.correct_answer || '',
                    }
                  : null
              }
              disabled={loading}
            />
          ) : (
            <>
              <div className={`bg-white rounded-3xl p-8 shadow-lg mb-6 transition-all duration-300
                ${phase === 'feedback' ? (isCorrect ? 'ring-4 ring-green-200' : 'ring-4 ring-red-200') : ''}`}>
                <div className="flex items-center gap-2 mb-4">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                    {currentQuestion?.skill_name || 'Matemáticas'}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
                    Nivel {currentQuestion?.difficulty_level || currentQuestion?.difficulty || 1}
                  </span>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">{currentQuestion?.question_text}</h2>

                {isNumeric ? (
                  <div className="space-y-3">
                    <input
                      type="text"
                      inputMode="numeric"
                      value={selectedAnswer || ''}
                      onChange={(e) => phase === 'testing' && setSelectedAnswer(e.target.value)}
                      disabled={phase === 'feedback'}
                      placeholder="Escribe tu respuesta..."
                      className={`w-full p-4 rounded-xl border-2 text-lg font-medium text-center transition
                        ${phase === 'feedback'
                          ? (isCorrect ? 'border-green-500 bg-green-50 text-green-700' : 'border-red-500 bg-red-50 text-red-700')
                          : 'border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 text-gray-700'}`}
                    />
                    {phase === 'feedback' && !isCorrect && (
                      <p className="text-sm text-gray-500 text-center">Respuesta correcta: <span className="font-semibold text-green-600">{currentQuestion?.correct_answer}</span></p>
                    )}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3">
                    {options.map((opt: string, idx: number) => {
                      const isSelected = selectedAnswer === opt;
                      const showResult = phase === 'feedback';
                      const isOptionCorrect = showResult && opt === currentQuestion?.correct_answer;
                      const isOptionWrong = showResult && isSelected && !isCorrect;

                      return (
                        <button key={idx}
                          onClick={() => phase === 'testing' && setSelectedAnswer(opt)}
                          disabled={phase === 'feedback'}
                          className={`p-4 rounded-xl border-2 text-left transition font-medium
                            ${isOptionCorrect ? 'border-green-500 bg-green-50 text-green-700' :
                              isOptionWrong ? 'border-red-500 bg-red-50 text-red-700' :
                              isSelected ? 'border-indigo-500 bg-indigo-50 text-indigo-700' :
                              'border-gray-200 hover:border-gray-300 text-gray-700'}`}>
                          <div className="flex items-center justify-between">
                            <span>{opt}</span>
                            {isOptionCorrect && <CheckCircle size={20} className="text-green-500" />}
                            {isOptionWrong && <XCircle size={20} className="text-red-500" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Feedback message */}
              {phase === 'feedback' && (
                <div className={`text-center p-4 rounded-2xl mb-4 ${isCorrect ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                  <p className="font-semibold text-lg">
                    {isCorrect ? '¡Excelente! 🌟' : '¡Sigue adelante! 💪'}
                  </p>
                  <p className="text-sm mt-1">
                    {isCorrect ? '¡Respuesta correcta!' : 'No te preocupes, esto nos ayuda a conocer tu nivel.'}
                  </p>
                </div>
              )}

              {/* Submit button */}
              {phase === 'testing' && (
                <button onClick={submitAnswer} disabled={!selectedAnswer || loading}
                  className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-semibold text-lg hover:bg-indigo-700 transition disabled:opacity-50">
                  {loading ? <Loader2 className="animate-spin mx-auto" /> : 'Confirmar Respuesta'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    );
  }

  // Results
  if (phase === 'results' && results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          <div className="w-20 h-20 bg-green-500 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <Star className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">¡Test Completado! 🎉</h1>
          <p className="text-gray-500 mb-8">Ya sabemos por dónde empezar tu aventura matemática</p>

          <div className="bg-white rounded-2xl p-6 shadow-lg mb-6">
            <div className="text-5xl font-bold text-indigo-600 mb-2">{results.score?.toFixed(0) || 0}%</div>
            <p className="text-gray-500">Puntuación general</p>

            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="p-4 bg-green-50 rounded-xl">
                <p className="text-2xl font-bold text-green-600">{results.correct_answers || 0}</p>
                <p className="text-sm text-gray-500">Correctas</p>
              </div>
              <div className="p-4 bg-blue-50 rounded-xl">
                <p className="text-2xl font-bold text-blue-600">{results.total_questions || 0}</p>
                <p className="text-sm text-gray-500">Total</p>
              </div>
            </div>

            {results.category_scores && (
              <div className="mt-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-3">Resultados por Área</h3>
                <div className="space-y-2">
                  {Object.entries(results.category_scores).map(([cat, score]: [string, any]) => (
                    <div key={cat} className="flex items-center gap-3">
                      <span className="text-xs text-gray-500 w-28 truncate capitalize">{cat}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                        <div className={`h-full rounded-full ${score >= 80 ? 'bg-green-500' : score >= 50 ? 'bg-amber-400' : 'bg-red-400'}`}
                          style={{ width: `${score}%` }} />
                      </div>
                      <span className="text-xs font-medium w-10 text-right">{score?.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button onClick={() => navigate('/student')}
            className="px-8 py-4 bg-indigo-600 text-white rounded-2xl font-semibold text-lg hover:bg-indigo-700 transition">
            ¡Comenzar a Aprender! 🚀
          </button>
        </div>
      </div>
    );
  }

  return null;
}
