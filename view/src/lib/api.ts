/**
 * SmartDesk AI — Typed API Client
 * Wraps all 10 FastAPI backend endpoints.
 */

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  signal: string;
  file_id?: string;
}

export interface ProcessRequest {
  file_id?: string;
  chunk_size: number;
  chunk_overlap: number;
  do_reset?: 0 | 1;
}

export interface ProcessResponse {
  signal: string;
  inserted_chunks?: number;
  processed_files?: number;
}

export interface PushRequest {
  do_rest?: 0 | 1;
  page_size?: number;
}

export interface PushResponse {
  signal: string;
  inserted_count?: number;
}

export interface IndexInfoResponse {
  signal: string;
  collection_info?: Record<string, unknown>;
}

export interface SearchRequest {
  text: string;
  limit?: number;
}

export interface SearchResult {
  score: number;
  text: string;
}

export interface SearchResponse {
  signal: string;
  search_results?: SearchResult[];
}

export interface AnswerResponse {
  signal: string;
  answer?: string;
  full_prompt?: string;
  chat_history?: unknown[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  signal: string;
  answer?: string;
  full_prompt?: string;
  conversation_history?: ChatMessage[];
  retrieved_documents?: SearchResult[];
}

export interface CloseConversationResponse {
  signal: string;
  conversation_id?: number;
}

export interface EmailTicketRequest {
  recipient_email: string;
  smtp_config: Record<string, unknown>;
}

export interface EmailTicketResponse {
  signal: string;
  conversation_id?: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ signal: `HTTP ${res.status}` }));
    throw new Error(err.signal || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ─── API Client ───────────────────────────────────────────────────────────────

export const api = {
  /** Health check */
  health: () => request<{ message: string }>('/api/v1/'),

  /** Upload a file (multipart/form-data) */
  upload: (projectId: number, file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${BASE}/api/v1/upload/${projectId}`, {
      method: 'POST',
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ signal: `HTTP ${res.status}` }));
        throw new Error(err.signal || `HTTP ${res.status}`);
      }
      return res.json();
    });
  },

  /** Process & chunk uploaded files */
  process: (projectId: number, body: ProcessRequest): Promise<ProcessResponse> =>
    request(`/api/v1/process/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** Embed chunks and push to vector DB */
  indexPush: (projectId: number, body: PushRequest): Promise<PushResponse> =>
    request(`/api/v1/nlp/index/push/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** Get vector collection metadata */
  indexInfo: (projectId: number): Promise<IndexInfoResponse> =>
    request(`/api/v1/nlp/index/info/${projectId}`),

  /** Semantic similarity search */
  search: (projectId: number, body: SearchRequest): Promise<SearchResponse> =>
    request(`/api/v1/nlp/index/search/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** Standard RAG: retrieve context + generate answer (no history) */
  answer: (projectId: number, body: SearchRequest): Promise<AnswerResponse> =>
    request(`/api/v1/nlp/index/answer/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** History-aware RAG chat with conversation persistence */
  chat: (projectId: number, body: SearchRequest): Promise<ChatResponse> =>
    request(`/api/v1/conversation/chat/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** Close the active conversation */
  closeConversation: (projectId: number): Promise<CloseConversationResponse> =>
    request(`/api/v1/conversation/chat/${projectId}/close`, { method: 'POST' }),

  /** Summarize conversation and email ticket to support team */
  emailTicket: (projectId: number, body: EmailTicketRequest): Promise<EmailTicketResponse> =>
    request(`/api/v1/conversation/chat/${projectId}/summarized_ticket_email`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
