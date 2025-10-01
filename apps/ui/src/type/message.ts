export type ChatMessage = {
  message: string;
  role: 'system' | 'user';
  interaction?: unknown;
};