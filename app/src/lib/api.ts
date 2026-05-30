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
    backend?: string;
  };
  embedding_model: string;
  llm_provider: string;
  feedback: {
    total: number;
    positive: number;
    neutral: number;
    negative: number;
    satisfaction: number | null;
  };
  validation_metrics: {
    mttr_reduction_target: string;
    knowledge_discovery_acceleration_target: string;
    documentation_maintenance_reduction_target: string;
    retrieval_precision_target?: string;
    answer_traceability_target?: string;
  };
  sla_targets: { uptime: string; p95_latency_ms: number };
  escalation?: {
    total: number;
    open: number;
    resolved: number;
    high_priority: number;
  };
  demo_readiness?: {
    seeded_knowledge: boolean;
    source_traceability: boolean;
    human_handoff: boolean;
    audit_logging: boolean;
    dlp_pii_controls: boolean;
  };
}

export interface EscalationResponse {
  ticket_id: string;
  external_ticket_id: string | null;
  status: string;
  priority: string;
  created_at: number;
  message: string;
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

export async function submitFeedback(
  sessionId: string,
  rating: -1 | 0 | 1,
  comment?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, rating, comment }),
  });
  if (!res.ok) throw new Error('Feedback failed');
}

export async function uploadDocument(file: File, title?: string): Promise<void> {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);
  const res = await fetch(`${API_BASE}/ingest`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
}

export async function createEscalation(params: {
  sessionId: string;
  query: string;
  aiResponse: string;
  sources: SourceCitation[];
  confidence: number;
  reason: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}): Promise<EscalationResponse> {
  const res = await fetch(`${API_BASE}/escalate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: params.sessionId,
      query: params.query,
      ai_response: params.aiResponse,
      sources: params.sources,
      confidence: params.confidence,
      reason: params.reason,
      priority: params.priority ?? 'medium',
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Escalation failed');
  }
  return res.json();
}
