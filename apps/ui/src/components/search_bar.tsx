'use client';
import { useState } from 'react';

type SearchBarProps = {
  callback: (message: string) => void;
};

export default function SearchBar({ callback }: SearchBarProps) {
  const [message, setMessages] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && message.trim() !== '') {
      callback(message);
      setMessages((prev) => '');
    }
  };

  return (
    <>
      <div>
        <input
          value={message}
          onChange={(e) => setMessages((prev) => e.target.value)}
          placeholder="Pergunte alguma coisa"
          className="pt-4 pb-4 pl-6 pr-6 rounded-xl bg-secondary_gray text-primary_gray outline-none caret-primary_gray w-full"
          onKeyDown={handleKeyDown}
        ></input>
      </div>
    </>
  );
}
