'use client';
import { useState } from 'react';

type SearchBarProps = {
  callback: (message: string) => void;
  disabled?: boolean;
};

export default function SearchBar({ callback, disabled = false }: SearchBarProps) {
  const [message, setMessages] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.key === 'Enter' && message.trim() !== '') {
      submit();
    }
  };

  const submit = () => {
    if (disabled) return;
    const payload = message.trim();
    if (!payload) return;
    callback(payload);
    setMessages('');
  };

  return (
    <>
      <div className="w-full flex items-center gap-2">
        <input
          value={message}
          onChange={(e) => setMessages(e.target.value)}
          placeholder="Pergunte alguma coisa"
          className="pt-4 pb-4 pl-6 pr-6 rounded-xl bg-secondary_gray text-primary_gray outline-none caret-primary_gray w-full disabled:opacity-60 disabled:cursor-not-allowed"
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <button
          onClick={submit}
          disabled={disabled || message.trim() === ''}
          className="px-5 py-3 rounded-xl bg-primary_blue hover:bg-primary_blue/80 transition text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {disabled ? (
            <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            'Enviar'
          )}
        </button>
      </div>
    </>
  );
}
