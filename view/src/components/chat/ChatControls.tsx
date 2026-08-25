'use client';

import styles from './ChatControls.module.css';

interface Props {
  isClosed: boolean;
  onCloseChat: () => void;
  onOpenEmailModal: () => void;
  isClosing: boolean;
  messageCount: number;
}

export default function ChatControls({
  isClosed,
  onCloseChat,
  onOpenEmailModal,
  isClosing,
  messageCount,
}: Props) {
  return (
    <div className={`glass-card ${styles.container}`}>
      <div className={styles.statusSection}>
        <span className="label">Session Status</span>
        <div className={styles.badgeRow}>
          <span className={`badge ${isClosed ? 'badge-closed' : 'badge-active'}`}>
            {isClosed ? 'Closed' : 'Active'}
          </span>
          <span className={styles.msgCount}>{messageCount} messages</span>
        </div>
      </div>

      <div className={styles.actions}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={onOpenEmailModal}
          disabled={messageCount === 0}
          title="Summarize conversation & email ticket"
          style={{ width: '100%' }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
          Email Support Ticket
        </button>

        {!isClosed && (
          <button
            className="btn btn-danger btn-sm"
            onClick={onCloseChat}
            disabled={isClosing || messageCount === 0}
            title="Mark session as closed"
            style={{ width: '100%' }}
          >
            {isClosing ? (
              <>
                <span className="spinner spinner-sm" /> Closing…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                Close Conversation
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
