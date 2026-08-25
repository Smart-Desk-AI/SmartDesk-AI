'use client';

import { useState } from 'react';
import { useProject } from '@/context/ProjectContext';
import { api } from '@/lib/api';
import TopBar from '@/components/layout/TopBar';
import QueryInput from '@/components/rag/QueryInput';
import AnswerPanel from '@/components/rag/AnswerPanel';
import styles from './page.module.css';

export default function RagPage() {
  const { projectId } = useProject();
  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [fullPrompt, setFullPrompt] = useState<string | null>(null);
  const [toasts, setToasts] = useState<{ id: number; msg: string; type: 'success' | 'error' | 'info' }[]>([]);

  const addToast = (msg: string, type: 'success' | 'error' | 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, msg, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const handleSearch = async (query: string, limit: number) => {
    setIsLoading(true);
    setAnswer(null);
    setFullPrompt(null);

    try {
      const res = await api.answer(projectId, { text: query, limit });
      if (res.answer) {
        setAnswer(res.answer);
        setFullPrompt(res.full_prompt || null);
        addToast('Answer generated successfully!', 'success');
      } else {
        addToast(`Could not generate answer. Signal: ${res.signal}`, 'warning' as 'error');
      }
    } catch (e: unknown) {
      addToast(`Search failed: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <TopBar title="Document Q&A" subtitle="Single-turn Standard RAG" />

      <main className={`page-content ${styles.main}`}>
        <div className={styles.splitLayout}>
          <div className={styles.leftCol}>
            <QueryInput onSubmit={handleSearch} isLoading={isLoading} />
          </div>
          <div className={styles.rightCol}>
            <AnswerPanel answer={answer} fullPrompt={fullPrompt} isLoading={isLoading} />
          </div>
        </div>
      </main>

      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            {t.msg}
          </div>
        ))}
      </div>
    </div>
  );
}
