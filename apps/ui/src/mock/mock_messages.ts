import { ChatMessage } from '@/type/message';

export function mockMessages(): ChatMessage[] {
  return [
    { role: 'system', message: 'Bem-vindo ao assistente virtual!' },
    { role: 'user', message: 'Oi, poderia me ajudar?' },
    { role: 'system', message: 'Claro! Qual é a sua dúvida?' },
    { role: 'user', message: 'Quero saber como alterar minha senha.' },
    {
      role: 'system',
      message: 'Você pode alterar sua senha no menu de configurações.',
    },
    { role: 'user', message: 'Não estou encontrando essa opção.' },
    {
      role: 'system',
      message: 'Ok, clique no ícone do seu perfil no canto superior direito.',
    },
    {
      role: 'system',
      message: "Depois selecione 'Segurança' e clique em 'Alterar senha'.",
    },
    { role: 'user', message: 'Ah, agora achei! Muito obrigado.' },
    { role: 'system', message: 'De nada! Deseja mais alguma ajuda?' },
    { role: 'user', message: 'Não, está ótimo.' },
    { role: 'system', message: 'Beleza, estarei aqui se precisar novamente.' },
    { role: 'user', message: 'Valeu, até mais!' },
    { role: 'system', message: 'Até logo! 👋' },
    { role: 'system', message: 'Conversa finalizada.' },
    { role: 'user', message: 'Ok.' },
    { role: 'system', message: 'Registro salvo com sucesso.' },
    { role: 'user', message: 'Perfeito.' },
    { role: 'system', message: 'Posso encerrar sua sessão agora?' },
    { role: 'user', message: 'Sim.' },
    { role: 'system', message: 'Sessão encerrada com segurança.' },
    { role: 'system', message: 'Obrigado por usar o sistema.' },
    { role: 'user', message: '👍' },
    { role: 'system', message: 'Tenha um ótimo dia!' },
    { role: 'user', message: 'Igualmente!' },
    { role: 'system', message: 'Assistente desconectado.' },
    { role: 'user', message: 'Tchau.' },
    { role: 'system', message: 'Tchau 👋' },
  ];
}
