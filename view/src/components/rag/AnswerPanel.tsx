'use client';

import { useState } from 'react';
import styles from './AnswerPanel.module.css';

interface Props {
  answer: string | null;
  fullPrompt: string | null;
  isLoading: boolean;
}

export default function AnswerPanel({ answer, fullPrompt, isLoading }: Props) {
  const [showPrompt, setShowPrompt] = useState(false);

  if (!answer && !isLoading) {
    return (
      <div className={`glass-card ${styles.card} ${styles.empty}`}>
        <div className={styles.emptyIcon}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
          </svg>
        </div>
        <p>Ask a question to see the AI's response here.</p>
      </div>
    );
  }

  return (
    <div className={`glass-card ${styles.card}`}>
      {isLoading ? (
        <div className={styles.loadingState}>
          <div className="spinner spinner-lg" />
          <p>Generating answer...</p>
        </div>
      ) : (
        <div className={styles.content}>
          <div className={styles.answerSection}>
            <h3 className={styles.title}>AI Answer</h3>
            <div className={styles.bubble}>
              <p className={styles.answerText}>{answer}</p>
            </div>
          </div>

          {fullPrompt && (
            <div className={styles.promptSection}>
              <button
                className={styles.toggleBtn}
                onClick={() => setShowPrompt(!showPrompt)}
              >
                <span className={styles.toggleIcon} style={{ transform: showPrompt ? 'rotate(90deg)' : 'none' }}>
                  ▶
                </span>
                {showPrompt ? 'Hide Full Prompt Context' : 'View Full Prompt Context'}
              </button>

              {showPrompt && (
                <pre className={styles.codeBlock}>{fullPrompt}</pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
