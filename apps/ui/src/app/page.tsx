'use client';

import Message from '@/components/message';
import SearchBar from '@/components/search_bar';
import { mockMessages } from '@/mock/mock_messages';
import { ChatMessage } from '@/type/message';
import { useEffect, useRef, useState } from 'react';

export default function Page() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const updateMessages = async (message: string): Promise<void> => {
    setMessages((prev) => [
      ...prev,
      { role: 'user', message },
      { role: 'system', message: '...' },
    ]);

    try {
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
        systemMessage = { role: 'system', message: content.message.message };
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
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <>
      <main className="overflow-hidden bg-background w-full min-h-screen flex items-center flex-col pt-20">
        <section className="w-[800px] flex flex-col gap-4 mb-60">
          {messages.map((msg, index) => (
            <>
              <Message key={index} message={msg.message} role={msg.role} />
              <hr className="border-secondary_gray text" />
            </>
          ))}
          <div ref={bottomRef} />
        </section>
        <div className="w-main_content_width fixed bottom-20">
          <SearchBar callback={updateMessages} />
        </div>
      </main>
    </>
  );
}
