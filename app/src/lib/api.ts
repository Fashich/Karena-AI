const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export interface SourceCitation {
  id: string;
  title: string;
  source_id: string;
  excerpt: string;
  score: number;
  channel: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  confidence: number;
  session_id: string;
  latency_ms: number;
}

export interface AdminStats {
  tenant_id: string;
  environment: string;
  vector_db: {
    healthy: boolean;
    collection: string;
    points_count: number;
  };
  embedding_model: string;
  llm_provider: string;
  sla_targets: { uptime: string; p95_latency_ms: number };
}

export async function sendChat(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Chat request failed');
  }
  return res.json();
}

export async function fetchAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${API_BASE}/admin/stats`);
  if (!res.ok) throw new Error('Failed to load admin stats');
  return res.json();
}

export async function fetchHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function uploadDocument(file: File, title?: string): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);
  const res = await fetch(`${API_BASE}/ingest`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
}
