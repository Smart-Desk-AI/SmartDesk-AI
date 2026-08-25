'use client';

import { useState } from 'react';
import { useProject } from '@/context/ProjectContext';
import TopBar from '@/components/layout/TopBar';
import UploadCard from '@/components/dashboard/UploadCard';
import ProcessCard from '@/components/dashboard/ProcessCard';
import IndexCard from '@/components/dashboard/IndexCard';
import StatusCard from '@/components/dashboard/StatusCard';
import styles from './page.module.css';

export default function DashboardPage() {
  const { projectId } = useProject();
  const [fileId, setFileId] = useState<string | null>(null);
  const [toasts, setToasts] = useState<{ id: number; msg: string; type: 'success' | 'error' | 'info' }[]>([]);

  const addToast = (msg: string, type: 'success' | 'error' | 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, msg, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  return (
    <div className={styles.container}>
      <TopBar title="Dashboard" subtitle="Manage your Knowledge Base" />

      <main className="page-content">
        <div className={styles.grid}>
          <div className={styles.col}>
            <UploadCard
              projectId={projectId}
              onUploadSuccess={setFileId}
              onToast={addToast}
            />
            <ProcessCard
              projectId={projectId}
              fileId={fileId}
              onProcessSuccess={() => {}}
              onToast={addToast}
            />
          </div>
          <div className={styles.col}>
            <IndexCard
              projectId={projectId}
              onIndexSuccess={() => {}}
              onToast={addToast}
            />
            <StatusCard
              projectId={projectId}
              onToast={addToast}
            />
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
