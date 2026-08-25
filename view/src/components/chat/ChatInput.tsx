'use client';

import { useState, KeyboardEvent } from 'react';
import styles from './ChatInput.module.css';

interface Props {
  onSend: (msg: string) => void;
  isDisabled: boolean;
  isClosed: boolean;
}

export default function ChatInput({ onSend, isDisabled, isClosed }: Props) {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (text.trim() && !isDisabled && !isClosed) {
      onSend(text);
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={`glass-card ${styles.container}`}>
      <textarea
        className={styles.textarea}
        placeholder={isClosed ? 'Conversation closed.' : 'Type your message... (Press Enter to send)'}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isDisabled || isClosed}
        rows={1}
      />
      <button
        className={styles.sendBtn}
        onClick={handleSend}
        disabled={!text.trim() || isDisabled || isClosed}
        title="Send Message"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
  );
}
