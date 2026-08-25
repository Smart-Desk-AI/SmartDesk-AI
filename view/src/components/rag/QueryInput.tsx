'use client';

import { useState } from 'react';
import styles from './QueryInput.module.css';

interface Props {
  onSubmit: (query: string, limit: number) => void;
  isLoading: boolean;
}

export default function QueryInput({ onSubmit, isLoading }: Props) {
  const [query, setQuery] = useState('');
  const [limit, setLimit] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query, limit);
    }
  };

  return (
    <div className={`glass-card ${styles.card}`}>
      <h2 className={styles.title}>Ask a Question</h2>
      <p className={styles.desc}>Get answers grounded in your indexed document chunks.</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className="form-group">
          <label className="label">Your Query</label>
          <textarea
            className={`input ${styles.textarea}`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What is the refund policy?"
            disabled={isLoading}
            rows={4}
          />
        </div>

        <div className={styles.sliderGroup}>
          <div className={styles.sliderRow}>
            <label className="label">Context Limit</label>
            <span className={styles.sliderValue}>{limit} docs</span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className={styles.slider}
            disabled={isLoading}
          />
          <p className={styles.hint}>Number of chunks to retrieve and inject into the prompt.</p>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!query.trim() || isLoading}
          style={{ width: '100%', marginTop: 'var(--space-4)' }}
        >
          {isLoading ? <><span className="spinner spinner-sm" /> Searching…</> : 'Search & Answer'}
        </button>
      </form>
    </div>
  );
}
