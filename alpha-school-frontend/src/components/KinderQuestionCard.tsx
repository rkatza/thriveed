import { useState, useEffect, useRef, useCallback } from 'react';
import { Volume2, CheckCircle, XCircle } from 'lucide-react';

interface OptionMedia {
  id: string;
  label: string;
  image: string;
  audio_url?: string;
}

interface KinderQuestionCardProps {
  question: {
    id: number;
    question_text: string;
    question_image_url?: string;
    question_audio_url?: string;
    audio_duration_ms?: number;
    options?: string[];
    options_media?: OptionMedia[];
    grade_level?: string;
    locale?: string;
  };
  onAnswer: (answer: string) => void;
  feedback?: {
    is_correct: boolean;
    correct_answer: string;
    explanation?: string;
  } | null;
  disabled?: boolean;
}

/**
 * KinderQuestionCard — Visual-first, audio-first question component for kindergarten.
 *
 * Design principles (PRD §14):
 *  - NO text reading required — everything is visual (emoji/images) + audio
 *  - Auto-play question audio on load
 *  - Large tap targets (≥64dp) for small fingers
 *  - Single tap to preview option, double-tap / confirm button to submit
 *  - "Escuchar otra vez" replay button (≥64×64dp)
 *  - Locale: es-419 (Latin American Spanish)
 */
export default function KinderQuestionCard({
  question,
  onAnswer,
  feedback,
  disabled,
}: KinderQuestionCardProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [hasSpoken, setHasSpoken] = useState(false);
  const speechRef = useRef<SpeechSynthesisUtterance | null>(null);
  const hasMountedRef = useRef(false);

  // ─── TTS helper ───────────────────────────────────────
  const speak = useCallback(
    (text: string) => {
      if (!text) return;
      window.speechSynthesis.cancel();

      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = question.locale || 'es-419';
      utter.rate = 0.85; // slower for kids
      utter.pitch = 1.1; // slightly higher / friendlier

      // Try to pick a Spanish voice
      const voices = window.speechSynthesis.getVoices();
      const esVoice = voices.find(
        (v) =>
          v.lang.startsWith('es-MX') ||
          v.lang.startsWith('es-419') ||
          v.lang.startsWith('es-US') ||
          v.lang.startsWith('es'),
      );
      if (esVoice) utter.voice = esVoice;

      speechRef.current = utter;
      window.speechSynthesis.speak(utter);
    },
    [question.locale],
  );

  // Auto-speak question on mount / when question changes
  useEffect(() => {
    setSelectedOption(null);
    setHasSpoken(false);
    hasMountedRef.current = false;
  }, [question.id]);

  useEffect(() => {
    if (hasMountedRef.current || hasSpoken) return;
    hasMountedRef.current = true;

    // Small delay so the card is visible before audio starts
    const timer = setTimeout(() => {
      speak(question.question_text);
      setHasSpoken(true);
    }, 600);

    return () => clearTimeout(timer);
  }, [question.id, hasSpoken, speak, question.question_text]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  // Load voices (some browsers need this)
  useEffect(() => {
    window.speechSynthesis.getVoices();
    const onVoices = () => window.speechSynthesis.getVoices();
    window.speechSynthesis.addEventListener('voiceschanged', onVoices);
    return () => window.speechSynthesis.removeEventListener('voiceschanged', onVoices);
  }, []);

  // ─── Handlers ─────────────────────────────────────────
  const handleOptionTap = (opt: OptionMedia) => {
    if (disabled || feedback) return;
    // Speak the option label
    speak(opt.label);
    setSelectedOption(opt.id);
  };

  const handleConfirm = () => {
    if (!selectedOption || disabled || feedback) return;
    onAnswer(selectedOption);
  };

  const handleReplay = () => {
    speak(question.question_text);
  };

  // ─── Determine options to render ──────────────────────
  const optionsMedia: OptionMedia[] = question.options_media || [];
  const hasVisualOptions = optionsMedia.length > 0;

  // Feedback state helpers
  const showFeedback = feedback !== null && feedback !== undefined;
  const isCorrect = showFeedback && feedback?.is_correct;

  return (
    <div className="w-full max-w-xl mx-auto">
      {/* ── Question visual ── */}
      <div
        className={`bg-white rounded-3xl p-6 shadow-lg mb-4 transition-all duration-300 ${
          showFeedback
            ? isCorrect
              ? 'ring-4 ring-green-300'
              : 'ring-4 ring-red-300'
            : ''
        }`}
      >
        {/* Big visual prompt */}
        {question.question_image_url && (
          <div className="text-center mb-4">
            <span className="text-6xl md:text-7xl leading-tight select-none">
              {question.question_image_url}
            </span>
          </div>
        )}

        {/* Replay / listen button */}
        <button
          onClick={handleReplay}
          className="mx-auto flex items-center gap-2 px-5 py-3 bg-indigo-100 text-indigo-700 rounded-2xl font-semibold text-base hover:bg-indigo-200 active:scale-95 transition min-h-[48px] min-w-[48px]"
          aria-label="Escuchar otra vez"
        >
          <Volume2 size={24} />
          <span className="text-lg">Escuchar</span>
        </button>
      </div>

      {/* ── Options grid ── */}
      {hasVisualOptions && (
        <div
          className={`grid gap-3 mb-4 ${
            optionsMedia.length <= 2 ? 'grid-cols-2' : 'grid-cols-2'
          }`}
        >
          {optionsMedia.map((opt) => {
            const isSelected = selectedOption === opt.id;
            const isOptionCorrect =
              showFeedback && opt.id === feedback?.correct_answer;
            const isOptionWrong =
              showFeedback && isSelected && !feedback?.is_correct;

            return (
              <button
                key={opt.id}
                onClick={() => handleOptionTap(opt)}
                disabled={!!feedback || disabled}
                className={`relative flex flex-col items-center justify-center p-4 rounded-2xl border-3 transition-all duration-200 min-h-[100px] active:scale-95
                  ${
                    isOptionCorrect
                      ? 'border-green-500 bg-green-50 ring-2 ring-green-300'
                      : isOptionWrong
                        ? 'border-red-500 bg-red-50 ring-2 ring-red-300'
                        : isSelected
                          ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-300 shadow-md'
                          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                  }
                `}
              >
                {/* Emoji visual */}
                <span className="text-4xl md:text-5xl mb-1 select-none">
                  {opt.image}
                </span>

                {/* Feedback icons */}
                {isOptionCorrect && (
                  <CheckCircle
                    size={28}
                    className="absolute top-2 right-2 text-green-500"
                  />
                )}
                {isOptionWrong && (
                  <XCircle
                    size={28}
                    className="absolute top-2 right-2 text-red-500"
                  />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* ── Feedback banner ── */}
      {showFeedback && (
        <div
          className={`text-center p-4 rounded-2xl mb-4 ${
            isCorrect
              ? 'bg-green-100 text-green-700'
              : 'bg-amber-100 text-amber-700'
          }`}
        >
          <p className="font-bold text-2xl">
            {isCorrect ? '¡Muy bien! 🌟' : '¡Intenta otra vez! 💪'}
          </p>
        </div>
      )}

      {/* ── Confirm button (only when option selected, no feedback yet) ── */}
      {!showFeedback && selectedOption && (
        <button
          onClick={handleConfirm}
          disabled={disabled}
          className="w-full py-5 bg-indigo-600 text-white rounded-2xl font-bold text-xl hover:bg-indigo-700 active:scale-[0.98] transition disabled:opacity-50 shadow-lg"
        >
          ✅ Confirmar
        </button>
      )}
    </div>
  );
}
