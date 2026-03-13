import type { Metadata } from 'next';
import { Inter, DM_Serif_Display } from 'next/font/google';
import { QueryProvider } from '@/lib/queryClient';
import { ToastContainer } from '@/components/ui/Toast';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const dmSerif = DM_Serif_Display({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-dm-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'FitGenix - AI-Powered Fitness & Lifestyle Platform',
  description: 'Transform your health with personalized AI-driven workout plans, nutrition guidance, and lifestyle optimization.',
  keywords: ['fitness', 'health', 'AI', 'workout', 'nutrition', 'lifestyle'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${dmSerif.variable}`}>
      <body className="font-sans antialiased bg-bg-base text-text-primary min-h-screen">
        <QueryProvider>
          {children}
          <ToastContainer />
        </QueryProvider>
      </body>
    </html>
  );
}
