import { useState, useCallback, useRef } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface SpeakButtonProps {
  text: string;
  lang?: string;
  className?: string;
  size?: number;
  autoSpeak?: boolean;
}

export default function SpeakButton({ text, lang = 'es-MX', className = '', size = 20, autoSpeak = false }: SpeakButtonProps) {
  const [speaking, setSpeaking] = useState(false);
  const hasAutoSpoken = useRef(false);

  const speak = useCallback(() => {
    if (!text) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 0.85; // Slightly slower for kids
    utterance.pitch = 1.1; // Slightly higher pitch, friendlier

    // Try to find a Spanish voice
    const voices = window.speechSynthesis.getVoices();
    const spanishVoice = voices.find(v => v.lang.startsWith('es'));
    if (spanishVoice) {
      utterance.voice = spanishVoice;
    }

    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }, [text, lang]);

  // Auto-speak on first render for kinder students
  if (autoSpeak && text && !hasAutoSpoken.current) {
    hasAutoSpoken.current = true;
    // Small delay to let component mount
    setTimeout(speak, 300);
  }

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  return (
    <button
      onClick={speaking ? stop : speak}
      className={`inline-flex items-center justify-center gap-1.5 rounded-xl transition ${
        speaking
          ? 'bg-indigo-100 text-indigo-700 animate-pulse'
          : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
      } ${className}`}
      aria-label={speaking ? 'Detener lectura' : 'Leer en voz alta'}
      title={speaking ? 'Detener' : 'Escuchar pregunta'}
    >
      {speaking ? <VolumeX size={size} /> : <Volume2 size={size} />}
      <span className="text-sm font-medium">{speaking ? 'Parar' : 'Escuchar'}</span>
    </button>
  );
}
