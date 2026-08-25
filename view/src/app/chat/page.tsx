'use client';

import { useState } from 'react';
import { useProject } from '@/context/ProjectContext';
import { api, ChatMessage, SearchResult } from '@/lib/api';
import TopBar from '@/components/layout/TopBar';
import ChatWindow from '@/components/chat/ChatWindow';
import ChatInput from '@/components/chat/ChatInput';
import ChatControls from '@/components/chat/ChatControls';
import SourceDrawer from '@/components/chat/SourceDrawer';
import EmailModal from '@/components/chat/EmailModal';
import styles from './page.module.css';

export default function ChatPage() {
  const { projectId } = useProject();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [retrievedDocs, setRetrievedDocs] = useState<SearchResult[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [isEmailing, setIsEmailing] = useState(false);
  const [isClosed, setIsClosed] = useState(false);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [toasts, setToasts] = useState<{ id: number; msg: string; type: 'success' | 'error' | 'info' }[]>([]);

  const addToast = (msg: string, type: 'success' | 'error' | 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, msg, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const handleSendMessage = async (query: string) => {
    // Optimistically add user message
    const userMsg: ChatMessage = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await api.chat(projectId, { text: query });

      if (res.conversation_history && res.conversation_history.length > 0) {
        setMessages(res.conversation_history);
      } else if (res.answer) {
        setMessages((prev) => [...prev, { role: 'assistant', content: res.answer! }]);
      }

      if (res.retrieved_documents) {
        setRetrievedDocs(res.retrieved_documents);
      }
    } catch (e: unknown) {
      addToast(`Chat error: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsSending(false);
    }
  };

  const handleCloseConversation = async () => {
    setIsClosing(true);
    try {
      const res = await api.closeConversation(projectId);
      setIsClosed(true);
      addToast(`Conversation closed (ID: ${res.conversation_id})`, 'info');
    } catch (e: unknown) {
      addToast(`Failed to close conversation: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsClosing(false);
    }
  };

  const handleSendEmailTicket = async (recipientEmail: string) => {
    setIsEmailing(true);
    try {
      await api.emailTicket(projectId, {
        recipient_email: recipientEmail,
        smtp_config: {},
      });
      addToast(`Support ticket summarized and emailed to ${recipientEmail}!`, 'success');
      setIsEmailModalOpen(false);
    } catch (e: unknown) {
      addToast(`Failed to email ticket: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
    } finally {
      setIsEmailing(false);
    }
  };

  return (
    <div className={styles.container}>
      <TopBar title="Conversational AI Chat" subtitle="Multi-turn History-Aware Support" />

      <main className={`page-content ${styles.main}`}>
        <div className={styles.chatLayout}>
          {/* Main Chat Center Column */}
          <div className={styles.centerCol}>
            <ChatWindow messages={messages} isLoading={isSending} />
            <ChatInput
              onSend={handleSendMessage}
              isDisabled={isSending}
              isClosed={isClosed}
            />
          </div>

          {/* Right Sidebar: Controls & Retrieved Context */}
          <div className={styles.rightCol}>
            <ChatControls
              isClosed={isClosed}
              onCloseChat={handleCloseConversation}
              onOpenEmailModal={() => setIsEmailModalOpen(true)}
              isClosing={isClosing}
              messageCount={messages.length}
            />
            <SourceDrawer documents={retrievedDocs} />
          </div>
        </div>
      </main>

      <EmailModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        onSend={handleSendEmailTicket}
        isSending={isEmailing}
      />

      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`}>
            {t.msg}
          </div>
        ))}
      </div>
    </div>
  );
}
