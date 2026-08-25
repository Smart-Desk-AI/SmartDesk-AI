'use client';

import { useEffect, useRef } from 'react';
import { ChatMessage } from '@/lib/api';
import styles from './ChatWindow.module.css';

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
}

export default function ChatWindow({ messages, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <p>No active conversation. Send a message to start a new session.</p>
      </div>
    );
  }

  return (
    <div className={styles.window}>
      {messages.map((msg, i) => {
        // Skip system prompts in the UI
        if (msg.role === 'system') return null;

        const isUser = msg.role === 'user';
        return (
          <div key={i} className={`${styles.messageWrapper} ${isUser ? styles.wrapperUser : styles.wrapperAssistant}`}>
            {!isUser && (
              <div className={styles.avatar}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
            )}
            <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant}`}>
              {msg.content}
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className={`${styles.messageWrapper} ${styles.wrapperAssistant}`}>
          <div className={styles.avatar}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className={`${styles.bubble} ${styles.bubbleAssistant} ${styles.bubbleLoading}`}>
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
            <span className={styles.dot}></span>
          </div>
        </div>
      )}
      
      <div ref={bottomRef} />
    </div>
  );
}
