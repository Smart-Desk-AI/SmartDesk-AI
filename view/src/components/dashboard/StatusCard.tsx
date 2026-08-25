'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import styles from './StatusCard.module.css';

interface Props {
  projectId: number;
  onToast: (msg: string, type: 'success' | 'error' | 'info') => void;
}

export default function StatusCard({ projectId, onToast }: Props) {
  const [info, setInfo] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStatus = async () => {
    setIsLoading(true);
    setInfo(null);
    try {
      const res = await api.indexInfo(projectId);
      setInfo(res.collection_info || null);
    } catch (e: unknown) {
      onToast(`Failed to fetch status: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`glass-card ${styles.card}`}>
      <div className={styles.header}>
        <div className={styles.stepBadge}>4</div>
        <div>
          <h3 className={styles.title}>Collection Status</h3>
          <p className={styles.desc}>View Vector DB collection metadata</p>
        </div>
      </div>

      <div className={styles.content}>
        <button className="btn btn-secondary" onClick={fetchStatus} disabled={isLoading} style={{ width: '100%' }}>
          {isLoading ? <><span className="spinner spinner-sm" /> Loading…</> : 'Fetch Collection Info'}
        </button>

        {info && (
          <div className={styles.infoBox}>
            <pre className={styles.codeBlock}>{JSON.stringify(info, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
