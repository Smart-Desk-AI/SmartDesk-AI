import type { Metadata } from 'next';
import './globals.css';
import { ProjectProvider } from '@/context/ProjectContext';
import Sidebar from '@/components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'SmartDesk AI — Intelligent Customer Support',
  description: 'AI-powered customer support platform with RAG, document Q&A, and multi-turn conversational AI.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ProjectProvider>
          <div className="app-shell">
            <Sidebar />
            <div className="app-main">{children}</div>
          </div>
        </ProjectProvider>
      </body>
    </html>
  );
}
