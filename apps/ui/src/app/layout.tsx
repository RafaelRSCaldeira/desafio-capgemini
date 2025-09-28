import './global.css';

export const metadata = {
  title: 'Desafio Capgemini',
  description: 'Desafio Capgemini - Chatbot',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
