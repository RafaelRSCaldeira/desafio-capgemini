import { ChatMessage } from "@/type/message";
import { marked } from "marked";
import DOMPurify from "isomorphic-dompurify";
import { useCallback } from "react";

export default function Message({ message, role, tts }: ChatMessage) {
  // Converter markdown em HTML
  const rawHtml = marked(message, { breaks: true, gfm: true }) as string;
  const safeHtml = DOMPurify.sanitize(rawHtml);

  const speak = useCallback(() => {
    try {
      const synth = window.speechSynthesis;
      if (!synth) return;
      const utter = new SpeechSynthesisUtterance(stripHtml(tts ?? message));
      utter.rate = 1.0;
      utter.pitch = 1.0;
      synth.cancel();
      synth.speak(utter);
    } catch (_) {
      // silencioso
    }
  }, [message]);

  const stop = useCallback(() => {
    try {
      const synth = window.speechSynthesis;
      if (!synth) return;
      synth.cancel();
    } catch (_) {
      // silencioso
    }
  }, []);

  const stripHtml = (html: string) => {
    if (typeof document === 'undefined') return html;
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  return (
    <div
      className={`${
        role === "user" ? "bg-primary_blue w-1/2 self-end" : "w-full"
      } break-words text-white text-lg p-4 rounded-md h-fit`}
    >
      {/* Renderizar como HTML, mas ainda funciona se for só texto normal */}
      <div className="flex items-start gap-2">
        <div className="flex-1" dangerouslySetInnerHTML={{ __html: safeHtml }} />
        {role === 'system' && (
          <div className="flex gap-1">
            <button
              aria-label="Ouvir resposta"
              onClick={speak}
              className="shrink-0 text-xs px-2 py-1 rounded border border-white/15 bg-white/5 text-white/70 hover:text-white"
              title="Ouvir resposta"
            >
              🔊
            </button>
            <button
              aria-label="Parar fala"
              onClick={stop}
              className="shrink-0 text-xs px-2 py-1 rounded border border-white/15 bg-white/5 text-white/70 hover:text-white"
              title="Parar fala"
            >
              ⏹️
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
