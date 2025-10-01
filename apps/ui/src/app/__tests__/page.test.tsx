import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Page from '@/app/page';

vi.mock('next/dynamic', async () => {
  const mod = await vi.importActual<any>('next/dynamic');
  return {
    __esModule: true,
    default: (imp: any) => imp().then((m: any) => m.default || m),
  };
});

describe('Page', () => {
  it('renders header', () => {
    render(<Page />);
    expect(screen.getByText('Cap Assistant')).toBeTruthy();
  });
});


