'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import styles from './ProcessCard.module.css';

interface Props {
  projectId: number;
  fileId: string | null;
  onProcessSuccess: () => void;
  onToast: (msg: string, type: 'success' | 'error' | 'info') => void;
}

export default function ProcessCard({ projectId, fileId, onProcessSuccess, onToast }: Props) {
  const [chunkSize, setChunkSize] = useState(500);
  const [overlap, setOverlap] = useState(50);
  const [doReset, setDoReset] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ files: number; chunks: number } | null>(null);

  const handleProcess = async () => {
    setIsLoading(true);
    setResult(null);
    try {
      const res = await api.process(projectId, {
        file_id: fileId || undefined,
        chunk_size: chunkSize,
        chunk_overlap: overlap,
        do_reset: doReset ? 1 : 0,
      });
      setResult({ files: res.processed_files ?? 0, chunks: res.inserted_chunks ?? 0 });
      onProcessSuccess();
      onToast(`Processed ${res.processed_files} file(s) → ${res.inserted_chunks} chunks created`, 'success');
    } catch (e: unknown) {
      onToast(`Processing failed: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`glass-card ${styles.card}`}>
      <div className={styles.header}>
        <div className={styles.stepBadge}>2</div>
        <div>
          <h3 className={styles.title}>Process & Chunk</h3>
          <p className={styles.desc}>Extract text and split into semantic chunks</p>
        </div>
      </div>

      <div className={styles.controls}>
        <div className={styles.sliderGroup}>
          <div className={styles.sliderRow}>
            <label className="label">Chunk Size</label>
            <span className={styles.sliderValue}>{chunkSize} chars</span>
          </div>
          <input type="range" min={100} max={2000} step={50} value={chunkSize}
            onChange={(e) => setChunkSize(Number(e.target.value))} className={styles.slider} />
        </div>

        <div className={styles.sliderGroup}>
          <div className={styles.sliderRow}>
            <label className="label">Overlap</label>
            <span className={styles.sliderValue}>{overlap} chars</span>
          </div>
          <input type="range" min={0} max={500} step={10} value={overlap}
            onChange={(e) => setOverlap(Number(e.target.value))} className={styles.slider} />
        </div>

        <label className={styles.checkRow}>
          <input type="checkbox" checked={doReset} onChange={(e) => setDoReset(e.target.checked)} className={styles.checkbox} />
          <span>Reset existing chunks before processing</span>
        </label>

        {fileId && (
          <p className={styles.fileHint}>
            Processing file ID: <code>{fileId}</code>
          </p>
        )}
      </div>

      {result && (
        <div className={styles.resultBanner}>
          <div className={styles.resultStat}>
            <span className={styles.statNum}>{result.files}</span>
            <span className={styles.statLabel}>Files</span>
          </div>
          <div className={styles.resultDivider} />
          <div className={styles.resultStat}>
            <span className={styles.statNum}>{result.chunks}</span>
            <span className={styles.statLabel}>Chunks</span>
          </div>
        </div>
      )}

      <button className="btn btn-primary" onClick={handleProcess} disabled={isLoading}
        style={{ marginTop: 'var(--space-5)', width: '100%' }}>
        {isLoading ? <><span className="spinner spinner-sm" /> Processing…</> : 'Process Documents'}
      </button>
    </div>
  );
}
