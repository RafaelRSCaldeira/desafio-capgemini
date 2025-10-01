import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import Message from '@/components/message';

describe('Message', () => {
  it('renders user message with blue bubble', () => {
    render(<Message role="user" message="Olá" />);
    const text = screen.getByText('Olá');
    expect(text).toBeTruthy();
  });

  it('renders system message with markdown', () => {
    render(<Message role="system" message={'**Negrito**'} />);
    const el = screen.getByText('Negrito');
    expect(el).toBeTruthy();
  });
});


