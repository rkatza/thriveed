import { useState, useCallback, useRef, useEffect } from 'react';
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
  const [voicesReady, setVoicesReady] = useState(false);
  const hasAutoSpoken = useRef(false);

  // Wait for voices to load (they load async in most browsers)
  useEffect(() => {
    if (!window.speechSynthesis) return;
    const check = () => {
      if (window.speechSynthesis.getVoices().length > 0) {
        setVoicesReady(true);
      }
    };
    check();
    window.speechSynthesis.addEventListener('voiceschanged', check);
    return () => window.speechSynthesis.removeEventListener('voiceschanged', check);
  }, []);

  const speak = useCallback(() => {
    if (!text || !window.speechSynthesis) return;

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

  // Auto-speak when text changes (for kinder students)
  useEffect(() => {
    // Reset flag first so every new text gets a chance to auto-speak
    hasAutoSpoken.current = false;

    if (autoSpeak && text && voicesReady) {
      hasAutoSpoken.current = true;
      const timer = setTimeout(speak, 300);
      return () => clearTimeout(timer);
    }
  }, [autoSpeak, text, voicesReady, speak]);

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
