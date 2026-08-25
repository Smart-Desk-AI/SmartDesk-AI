'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import styles from './IndexCard.module.css';

interface Props {
  projectId: number;
  onIndexSuccess: () => void;
  onToast: (msg: string, type: 'success' | 'error' | 'info') => void;
}

export default function IndexCard({ projectId, onIndexSuccess, onToast }: Props) {
  const [doReset, setDoReset] = useState(false);
  const [pageSize, setPageSize] = useState(50);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ count: number } | null>(null);

  const handleIndex = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await api.indexPush(projectId, {
        do_rest: doReset ? 1 : 0,
        page_size: pageSize,
      });
      setResult({ count: res.inserted_count ?? 0 });
      onIndexSuccess();
      onToast(`Successfully indexed ${res.inserted_count} chunks into Vector DB.`, 'success');
    } catch (e: unknown) {
      onToast(`Indexing failed: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`glass-card ${styles.card}`}>
      <div className={styles.header}>
        <div className={styles.stepBadge}>3</div>
        <div>
          <h3 className={styles.title}>Index to Vector DB</h3>
          <p className={styles.desc}>Embed chunks and push them to the vector database for RAG</p>
        </div>
      </div>

      <div className={styles.controls}>
        <div className={styles.formGroup}>
          <label className="label">Batch Page Size (Chunks)</label>
          <input
            type="number"
            min={10}
            max={500}
            step={10}
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            className="input"
          />
        </div>

        <label className={styles.checkRow}>
          <input type="checkbox" checked={doReset} onChange={(e) => setDoReset(e.target.checked)} className={styles.checkbox} />
          <span>Reset Vector DB collection before indexing</span>
        </label>
      </div>

      {result && (
        <div className={styles.resultBanner}>
          <div className={styles.resultStat}>
            <span className={styles.statNum}>{result.count}</span>
            <span className={styles.statLabel}>Indexed</span>
          </div>
        </div>
      )}

      <button className="btn btn-primary" onClick={handleIndex} disabled={isLoading}
        style={{ marginTop: 'var(--space-5)', width: '100%' }}>
        {isLoading ? <><span className="spinner spinner-sm" /> Indexing Vectors…</> : 'Push to Vector DB'}
      </button>
    </div>
  );
}
