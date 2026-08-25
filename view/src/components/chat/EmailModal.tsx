'use client';

import { useState } from 'react';
import styles from './EmailModal.module.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSend: (email: string) => Promise<void>;
  isSending: boolean;
}

export default function EmailModal({ isOpen, onClose, onSend, isSending }: Props) {
  const [email, setEmail] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    await onSend(email.trim());
    setEmail('');
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={`glass-card ${styles.modal}`} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.iconWrap}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <div>
            <h3 className={styles.title}>Send Ticket Summary</h3>
            <p className={styles.desc}>Summarizes conversation via LLM and sends via SMTP</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className="form-group">
            <label className="label">Recipient Email</label>
            <input
              type="email"
              className="input"
              placeholder="support-team@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSending}
              required
              autoFocus
            />
          </div>

          <div className={styles.actions}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!email.trim() || isSending}
            >
              {isSending ? (
                <>
                  <span className="spinner spinner-sm" /> Sending Ticket…
                </>
              ) : (
                'Summarize & Send'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
