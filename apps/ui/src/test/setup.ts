import { vi } from 'vitest'

// jsdom não implementa scrollIntoView; mock para evitar erro em testes
Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
  value: vi.fn(),
  writable: true,
})


