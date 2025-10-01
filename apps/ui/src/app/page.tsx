'use client';

import dynamic from 'next/dynamic';
const Message = dynamic(() => import('@/components/message'), { ssr: false });
import SearchBar from '@/components/search_bar';
import { ChatMessage } from '@/type/message';
import { useEffect, useRef, useState } from 'react';

export default function Page() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'test'>('chat');
  const [testOutput, setTestOutput] = useState<string>('');
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const updateMessages = async (message: string): Promise<void> => {
    setMessages((prev) => [
      ...prev,
      { role: 'user', message },
      { role: 'system', message: '...' },
    ]);

    try {
      setLoading(true);
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      let systemMessage: ChatMessage;

      if (!response.ok) {
        systemMessage = { role: 'system', message: 'Erro ao chamar a API' };
      } else {
        const content = await response.json();
        const mainMessage: string = content?.message?.message ?? '';
        const thinking: string | undefined = content?.message?.thinking;
        const rawData = content?.message?.interaction ?? "";

        // Escape HTML to safely embed inside <pre>
        const escapeHtml = (s: string) =>
          s
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        const thinkingBlock = thinking
          ? `\n\n<div class="mt-4">\n  <details class="group rounded-lg border border-white/10 bg-white/5">\n    <summary class="cursor-pointer select-none list-none px-3 py-2 flex items-center gap-2 text-sm text-white/80">\n      <svg class="h-3 w-3 text-white/60 transition-transform group-open:rotate-90" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M7.23 14.27a.75.75 0 0 1 0-1.06L10.44 10 7.23 6.79a.75.75 0 1 1 1.06-1.06l3.75 3.75a.75.75 0 0 1 0 1.06l-3.75 3.75a.75.75 0 0 1-1.06 0Z" clip-rule="evenodd"/></svg>\n      <span class="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide rounded bg-indigo-500/15 text-indigo-300/90 border border-indigo-500/20">Thinking</span>\n      <span>Mostrar raciocínio</span>\n    </summary>\n    <div class="border-t border-white/10">\n      <pre class="font-mono text-[12px] leading-5 whitespace-pre-wrap max-h-64 overflow-auto bg-[#0b1220] p-4 rounded-b-lg text-white/80">${escapeHtml(thinking)}</pre>\n      <div class="px-4 pb-3 text-[10px] text-white/40">Gerado pelo modelo; pode conter erros.</div>\n    </div>\n  </details>\n</div>`
          : '';

        const downloadJson = `\n\n<div class="mt-2">\n  <button id="download-json-${Date.now()}" class="text-[11px] px-2 py-1 rounded border border-white/15 bg-white/5 text-white/70 hover:text-white">⬇️ Baixar JSON</button>\n</div>`;

        systemMessage = { role: 'system', message: mainMessage + thinkingBlock + downloadJson, interaction: rawData };
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = systemMessage;
        console.log(updated);
        return updated;
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'system',
          message: 'Erro inesperado: ' + String(err),
        };
        return updated;
      });
    }
    finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <>
      <main className="relative min-h-screen w-full overflow-hidden bg-gradient-to-b from-[#0b1220] via-[#090f1a] to-black">
        {/* Soft background accents */}
        <div className="pointer-events-none absolute inset-0 [mask-image:radial-gradient(60%_50%_at_50%_0%,black,transparent)]">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-72 w-72 rounded-full bg-primary_blue/20 blur-3xl" />
          <div className="absolute top-40 right-10 h-56 w-56 rounded-full bg-indigo-500/10 blur-3xl" />
        </div>

        {/* Header */}
        <header className="w-full sticky top-0 z-10 backdrop-blur supports-[backdrop-filter]:bg-white/5">
          <div className="mx-auto max-w-[1000px] px-6 py-5">
            <h1 className="text-2xl md:text-3xl font-semibold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
              Cap Assistant
            </h1>
            <p className="text-sm text-white/50 mt-1">Pergunte sobre seus dados. O assistente prioriza a base interna e complementa com a web quando necessário.</p>
          </div>
        </header>

        {/* Tabs */}
        <div className="mx-auto mt-6 w-full max-w-[1000px] px-6">
          <div className="inline-flex rounded-xl border border-white/10 bg-white/5 p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                activeTab === 'chat' ? 'bg-primary_blue text-white' : 'text-white/70 hover:text-white'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('test')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                activeTab === 'test' ? 'bg-primary_blue text-white' : 'text-white/70 hover:text-white'
              }`}
            >
              Teste
            </button>
          </div>
        </div>

        {/* Content */}
        {activeTab === 'chat' && (
          <section className="mx-auto mt-4 mb-44 w-full max-w-[1000px] px-6">
            <div className="rounded-2xl border border-white/10 bg-white/5 shadow-2xl shadow-black/40">
              <div className="p-6 md:p-8 max-h-[68vh] overflow-y-auto flex flex-col gap-4">
                {messages.length === 0 && (
                  <div className="text-center py-16 text-white/70">
                    <h2 className="text-xl md:text-2xl font-medium">Bem-vindo(a)!</h2>
                    <p className="mt-2 text-sm md:text-base">Faça uma pergunta sobre seus CSVs (ex.: &quot;Qual o bônus total que Ana Souza recebeu em 2025?&quot;)</p>
                  </div>
                )}
                {messages.map((msg, index) => (
                  <div key={index} onClick={(e) => {
                    const target = e.target as HTMLElement;
                    if (target.id && target.id.startsWith('download-json-') && msg.role === 'system') {
                      const blob = new Blob([JSON.stringify(msg.interaction ?? {}, null, 2)], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `ai-response-${index}.json`;
                      document.body.appendChild(a);
                      a.click();
                      a.remove();
                      URL.revokeObjectURL(url);
                    }
                  }}>
                    <Message message={msg.message} role={msg.role} />
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
            </div>
          </section>
        )}

        {activeTab === 'test' && (
          <section className="mx-auto mt-4 mb-44 w-full max-w-[1000px] px-6">
            <div className="rounded-2xl border border-white/10 bg-white/5 shadow-2xl shadow-black/40 p-6 md:p-8">
              <h2 className="text-xl md:text-2xl font-medium text-white">Testes</h2>
              <p className="text-white/70 mt-2 text-sm md:text-base">Este projeto possui testes unitários e de integração para os serviços UI, AI e RAG.</p>
              <ul className="list-disc pl-6 mt-4 text-white/70 text-sm">
                <li>UI: Jest + Testing Library (componentes e integração básica)</li>
                <li>AI: Pytest com TestClient (mock de generate)</li>
                <li>RAG: Pytest validando busca por linhas e soma de bônus (Ana Souza 2025 = 2800)</li>
              </ul>

              <div className="mt-6 flex gap-3">
                <button
                  disabled={testLoading}
                  onClick={async () => {
                    setTestLoading(true);
                    setTestOutput('');
                    try {
                      const res = await fetch('/api/tests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: 'rag' }) });
                      const data = await res.json();
                      setTestOutput(data.output || JSON.stringify(data));
                    } catch (e) {
                      setTestOutput('Erro ao executar testes: ' + String(e));
                    } finally {
                      setTestLoading(false);
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-primary_blue text-white disabled:opacity-50"
                >
                  {testLoading ? 'Executando RAG...' : 'Executar testes RAG'}
                </button>

                <button
                  disabled={testLoading}
                  onClick={async () => {
                    setTestLoading(true);
                    setTestOutput('');
                    try {
                      const res = await fetch('/api/tests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: 'ai' }) });
                      const data = await res.json();
                      setTestOutput(data.output || JSON.stringify(data));
                    } catch (e) {
                      setTestOutput('Erro ao executar testes: ' + String(e));
                    } finally {
                      setTestLoading(false);
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-white/10 text-white disabled:opacity-50"
                >
                  {testLoading ? 'Executando AI...' : 'Executar testes AI'}
                </button>

                <button
                  disabled={testLoading}
                  onClick={async () => {
                    setTestLoading(true);
                    setTestOutput('');
                    try {
                      const res = await fetch('/api/tests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: 'all' }) });
                      const data = await res.json();
                      setTestOutput(data.output || JSON.stringify(data));
                    } catch (e) {
                      setTestOutput('Erro ao executar testes: ' + String(e));
                    } finally {
                      setTestLoading(false);
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-white/10 text-white disabled:opacity-50"
                >
                  {testLoading ? 'Executando todos...' : 'Executar todos'}
                </button>
                <button
                  disabled={testLoading}
                  onClick={async () => {
                    setTestLoading(true);
                    setTestOutput('');
                    try {
                      const res = await fetch('/api/tests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target: 'ui' as any }) });
                      const data = await res.json();
                      setTestOutput(data.output || JSON.stringify(data));
                    } catch (e) {
                      setTestOutput('Erro ao executar testes: ' + String(e));
                    } finally {
                      setTestLoading(false);
                    }
                  }}
                  className="px-4 py-2 rounded-lg bg-white/10 text-white disabled:opacity-50"
                >
                  {testLoading ? 'Executando UI...' : 'Executar testes UI'}
                </button>
              </div>

              <div className="mt-4">
                <label className="text-xs text-white/50">Saída</label>
                <pre className="mt-2 whitespace-pre-wrap text-xs bg-black/40 p-4 rounded-lg border border-white/10 text-white/80 max-h-[360px] overflow-auto">{testOutput || (testLoading ? 'Executando...' : 'Sem saída')}</pre>
              </div>
            </div>
          </section>
        )}

        {/* Composer */}
        {activeTab === 'chat' && (
          <div className="fixed inset-x-0 bottom-8 z-20">
            <div className="mx-auto w-full max-w-[900px] px-6">
              <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur px-4 py-3 shadow-xl shadow-black/40">
                <SearchBar callback={updateMessages} disabled={loading} />
              </div>
              <p className="text-[11px] text-white/40 mt-2 px-1">Dica: o agente usa RAG primeiro e complementa com web se necessário.</p>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
