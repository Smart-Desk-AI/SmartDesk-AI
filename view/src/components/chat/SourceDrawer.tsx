'use client';

import { SearchResult } from '@/lib/api';
import styles from './SourceDrawer.module.css';

interface Props {
  documents: SearchResult[];
}

export default function SourceDrawer({ documents }: Props) {
  if (!documents || documents.length === 0) {
    return (
      <div className={`glass-card ${styles.container} ${styles.empty}`}>
        <span className="label">Retrieved Context</span>
        <p className={styles.emptyText}>Source chunks retrieved for the latest turn will appear here.</p>
      </div>
    );
  }

  return (
    <div className={`glass-card ${styles.container}`}>
      <div className={styles.header}>
        <span className="label">Retrieved Context ({documents.length})</span>
      </div>
      <div className={styles.docList}>
        {documents.map((doc, idx) => (
          <div key={idx} className={styles.docCard}>
            <div className={styles.docMeta}>
              <span className={styles.docBadge}>Doc #{idx + 1}</span>
              {typeof doc.score === 'number' && (
                <span className={styles.docScore}>Score: {doc.score.toFixed(3)}</span>
              )}
            </div>
            <p className={styles.docText}>{doc.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
