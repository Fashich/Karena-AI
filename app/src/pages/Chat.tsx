import { useCallback, useRef, useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router';
import {
  ArrowUp,
  BookOpen,
  Camera,
  Download,
  Headphones,
  Loader2,
  ThumbsDown,
  ThumbsUp,
  X,
  LayoutDashboard,
  Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  sendChat,
  sendDomainQuery,
  analyzeImage,
  createEscalation,
  submitFeedback,
  type ChatResponse,
  type SourceCitation,
  type DomainQueryResponse,
  type MultimodalAnalysisResponse,
} from '@/lib/api';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  confidence?: number;
  latency_ms?: number;
  question?: string;
  escalationTicket?: string;
  escalationError?: string;
  isImageAnalysis?: boolean;
}

const DOMAINS = [
  { id: 'urban_mobility', label: 'Urban Mobility' },
  { id: 'healthcare', label: 'Healthcare' },
  { id: 'environment', label: 'Environment' },
  { id: 'citizen_services', label: 'Citizen Services' },
  { id: 'disaster_response', label: 'Disaster Response' },
  { id: 'education', label: 'Education' },
  { id: 'energy_utilities', label: 'Energy & Utilities' },
];

// ─── Sources list with collapse ──────────────────────────────
function SourcesList({ sources }: { sources: SourceCitation[] }) {
  const [expanded, setExpanded] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const TOP = 3;
  const visible = expanded ? sources : sources.slice(0, TOP);
  const rest = sources.length - TOP;

  return (
    <div className="mt-3 space-y-1.5 text-left">
      <p className="flex items-center gap-1 text-xs uppercase tracking-wider text-white/40">
        <BookOpen className="h-3 w-3" />
        Sources ({sources.length})
      </p>
      {visible.map((src) => (
        <button
          key={src.id}
          type="button"
          onClick={() => setOpenId(openId === src.id ? null : src.id)}
          className="block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-sm transition hover:border-white/20"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="truncate font-medium text-white/80 text-xs">{src.title}</span>
            <Badge variant="secondary" className="shrink-0 text-[10px]">
              {(src.score * 100).toFixed(0)}%
            </Badge>
          </div>
          {openId === src.id && src.excerpt && (
            <p className="mt-1.5 text-[11px] leading-relaxed text-white/50">{src.excerpt}</p>
          )}
        </button>
      ))}
      {rest > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="text-xs text-white/30 hover:text-white/60 transition px-1"
        >
          {expanded ? '▲ Show less' : `▼ Show ${rest} more sources`}
        </button>
      )}
    </div>
  );
}

export default function Chat() {
  const location = useLocation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>();
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [feedbackByMessage, setFeedbackByMessage] = useState<Record<string, -1 | 1>>(
    {}
  );
  const [escalatingMessage, setEscalatingMessage] = useState<string | null>(null);
  const [progressStep, setProgressStep] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Domain mode
  const [domainMode, setDomainMode] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<string>('urban_mobility');

  // Web search
  const [webSearch, setWebSearch] = useState(false);

  // Multimodal image
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageAnalyzing, setImageAnalyzing] = useState(false);

  // Pre-fill from navigation state (e.g. Dashboard "Ask AI" button)
  useEffect(() => {
    const state = location.state as { prefill?: string } | null;
    if (state?.prefill) setInput(state.prefill);
  }, [location.state]);

  const scrollToBottom = useCallback(() => {
    const el = scrollContainerRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    setTimeout(() => inputRef.current?.focus(), 300);
  }, []);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleImageAnalyze = async () => {
    if (!imageFile || imageAnalyzing) return;
    setImageAnalyzing(true);
    const context = input.trim() || 'Analyze this image for community impact and decision-making insights.';
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: `📷 Image analysis request: "${context}"`,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res: MultimodalAnalysisResponse = await analyzeImage(imageFile, context, selectedDomain);
      const actions = res.recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n');
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `${res.analysis}\n\n**Recommended Actions:**\n${actions}`,
          confidence: res.confidence > 0 ? res.confidence : undefined,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: `Image analysis error: ${err instanceof Error ? err.message : 'Failed'}` },
      ]);
    } finally {
      setImageAnalyzing(false);
      clearImage();
      setInput('');
      setTimeout(scrollToBottom, 100);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (imageFile) { handleImageAnalyze(); return; }
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setProgressStep('Classifying intent and tenant context');

    try {
      setTimeout(() => setProgressStep('Routing to domain specialist agent'), 200);
      setTimeout(() => setProgressStep('Retrieving dense and lexical matches'), 500);
      setTimeout(() => setProgressStep('Re-ranking sources and assembling citations'), 900);
      setTimeout(() => setProgressStep('Generating grounded answer with domain context'), 1300);

      let answer: string;
      let sources: SourceCitation[] = [];
      let confidence: number | undefined;
      let latency_ms: number | undefined;
      let newSessionId: string | undefined;
      let actions: string[] | undefined;

      if (domainMode) {
        const res: DomainQueryResponse = await sendDomainQuery(text, selectedDomain, sessionId);
        answer = res.answer;
        sources = res.sources;
        confidence = res.confidence;
        latency_ms = res.latency_ms;
        newSessionId = res.session_id;
        if (res.recommended_actions?.length) {
          actions = res.recommended_actions;
          answer += '\n\n**Recommended Actions:**\n' + actions.map((a, i) => `${i + 1}. ${a}`).join('\n');
        }
      } else {
        const res: ChatResponse = await sendChat(text, sessionId, webSearch);
        answer = res.answer;
        sources = res.sources;
        confidence = res.confidence;
        latency_ms = res.latency_ms;
        newSessionId = res.session_id;
      }

      if (newSessionId) setSessionId(newSessionId);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: answer,
          sources,
          confidence,
          latency_ms,
          question: text,
        },
      ]);
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Request failed'}. Ensure the backend is running.`,
        },
      ]);
    } finally {
      setLoading(false);
      setProgressStep(null);
    }
  };

  const suggestions = domainMode
    ? [
        `What are the key challenges in ${DOMAINS.find(d => d.id === selectedDomain)?.label ?? 'this domain'}?`,
        `How can AI improve decision-making in ${DOMAINS.find(d => d.id === selectedDomain)?.label ?? 'this area'}?`,
        'What data-driven interventions are most effective?',
      ]
    : [
        'What is our APAC data retention policy?',
        'Describe the Karena AI reference architecture',
        'When should support queries be escalated?',
      ];

  const handleFeedback = async (messageId: string, rating: -1 | 1) => {
    if (!sessionId) return;
    setFeedbackByMessage((prev) => ({ ...prev, [messageId]: rating }));
    try {
      await submitFeedback(sessionId, rating);
    } catch {
      setFeedbackByMessage((prev) => {
        const next = { ...prev };
        delete next[messageId];
        return next;
      });
    }
  };

  const handleEscalate = async (msg: Message) => {
    if (!sessionId || msg.role !== 'assistant') return;
    setEscalatingMessage(msg.id);
    try {
      const ticket = await createEscalation({
        sessionId,
        query: msg.question ?? 'Unspecified follow-up',
        aiResponse: msg.content,
        sources: msg.sources ?? [],
        confidence: msg.confidence ?? 0,
        reason:
          (msg.confidence ?? 1) < 0.7
            ? 'Low confidence or high-risk enterprise query'
            : 'User requested human expert review',
        priority: (msg.confidence ?? 1) < 0.5 ? 'high' : 'medium',
      });
      setMessages((prev) =>
        prev.map((item) =>
          item.id === msg.id
            ? { ...item, escalationTicket: ticket.ticket_id, escalationError: undefined }
            : item
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((item) =>
          item.id === msg.id
            ? {
                ...item,
                escalationError:
                  err instanceof Error ? err.message : 'Escalation failed',
              }
            : item
        )
      );
    } finally {
      setEscalatingMessage(null);
    }
  };

  const handleExport = (msg: Message) => {
    const sourceText = (msg.sources ?? [])
      .map(
        (source, index) =>
          `${index + 1}. ${source.title} (${source.channel}, ${Math.round(
            source.score * 100
          )}%)\n${source.excerpt}`
      )
      .join('\n\n');
    const body = [
      'Karena AI Response Export',
      '',
      `Question: ${msg.question ?? 'N/A'}`,
      '',
      `Answer:\n${msg.content}`,
      '',
      `Confidence: ${Math.round((msg.confidence ?? 0) * 100)}%`,
      `Latency: ${Math.round(msg.latency_ms ?? 0)}ms`,
      '',
      `Sources:\n${sourceText || 'No sources returned.'}`,
    ].join('\n');
    const blob = new Blob([body], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `karena-response-${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen flex-col bg-[#0a0a0f] text-white">
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3 gap-2 flex-wrap">
        <Link to="/" className="font-display text-base font-medium tracking-tight shrink-0">
          KARENA AI
        </Link>

        {/* Domain mode toggle */}
        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 p-1">
          <button
            type="button"
            onClick={() => setDomainMode(false)}
            className={cn(
              'rounded-md px-3 py-1 text-xs font-medium transition',
              !domainMode ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/70',
            )}
          >
            General
          </button>
          <button
            type="button"
            onClick={() => setDomainMode(true)}
            className={cn(
              'rounded-md px-3 py-1 text-xs font-medium transition',
              domainMode ? 'bg-white/15 text-white' : 'text-white/40 hover:text-white/70',
            )}
          >
            Domain AI
          </button>
        </div>

        {/* Web search toggle */}
        <button
          type="button"
          onClick={() => setWebSearch(w => !w)}
          title="Toggle web search"
          className={cn(
            'flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition',
            webSearch
              ? 'border-blue-500/50 bg-blue-500/15 text-blue-400'
              : 'border-white/10 bg-white/5 text-white/40 hover:text-white/70',
          )}
        >
          <span className="text-xs">??</span>
          {webSearch ? 'Web ON' : 'Web'}
        </button>

        {/* Domain selector (visible in domain mode) */}
        {domainMode && (
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value)}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs text-white/80 focus:outline-none"
          >
            {DOMAINS.map((d) => (
              <option key={d.id} value={d.id} className="bg-gray-900">
                {d.label}
              </option>
            ))}
          </select>
        )}

        <div className="flex items-center gap-2 ml-auto">
          {domainMode && (
            <Badge variant="outline" className="border-purple-500/50 text-purple-400 text-xs">
              <Layers className="mr-1 h-3 w-3" />
              {DOMAINS.find(d => d.id === selectedDomain)?.label}
            </Badge>
          )}
          <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 text-xs">
            RAG Active
          </Badge>
          <Link to="/dashboard">
            <Button variant="ghost" size="sm" className="text-white/60 h-7 px-2 text-xs">
              <LayoutDashboard className="h-3.5 w-3.5 mr-1" />
              Dashboard
            </Button>
          </Link>
          <Link to="/admin">
            <Button variant="ghost" size="sm" className="text-white/60 h-7 px-2 text-xs">
              Admin
            </Button>
          </Link>
        </div>
      </header>

      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-4 md:px-8"
      >
        <div className="mx-auto max-w-3xl py-8">
          {messages.length === 0 && (
            <div className="mb-12 text-center">
              <h1 className="font-display mb-3 text-3xl font-medium">
                {domainMode
                  ? `${DOMAINS.find(d => d.id === selectedDomain)?.label} AI Assistant`
                  : 'Community Decision Assistant'}
              </h1>
              <p className="mb-2 text-white/60">
                {domainMode
                  ? `Domain-specialist AI for ${DOMAINS.find(d => d.id === selectedDomain)?.label.toLowerCase()}. Ask questions, get insights, and receive data-driven recommendations.`
                  : 'Ask questions across your unified knowledge base. Upload images for AI-powered visual analysis.'}
              </p>
              {domainMode && (
                <p className="mb-6 text-xs text-purple-400/70">
                  Powered by RAG + multi-agent orchestration · Google ADK-ready
                </p>
              )}
              <div className="flex flex-wrap justify-center gap-2 mt-6">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setInput(s)}
                    className="rounded-full border border-white/15 px-4 py-2 text-sm text-white/80 transition hover:border-white/30 hover:bg-white/5"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                'mb-6',
                msg.role === 'user' ? 'text-right' : 'text-left'
              )}
            >
              <div
                className={cn(
                  'inline-block max-w-[90%] rounded-2xl px-5 py-3 text-left',
                  msg.role === 'user'
                    ? 'bg-white/10 text-white'
                    : 'bg-white/5 text-white/90'
                )}
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content}
                </p>
                {msg.role === 'assistant' && msg.confidence != null && (
                  <div className="mt-3 flex items-center gap-3 border-t border-white/10 pt-3 text-xs text-white/50">
                    <span>
                      Confidence: {(msg.confidence * 100).toFixed(0)}%
                    </span>
                    {msg.latency_ms != null && (
                      <span>{msg.latency_ms.toFixed(0)}ms</span>
                    )}
                    <button
                      type="button"
                      aria-label="Helpful"
                      title="Helpful"
                      onClick={() => handleFeedback(msg.id, 1)}
                      className={cn(
                        'transition hover:text-emerald-300',
                        feedbackByMessage[msg.id] === 1 && 'text-emerald-300'
                      )}
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      aria-label="Not helpful"
                      title="Not helpful"
                      onClick={() => handleFeedback(msg.id, -1)}
                      className={cn(
                        'transition hover:text-rose-300',
                        feedbackByMessage[msg.id] === -1 && 'text-rose-300'
                      )}
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      aria-label="Export response"
                      title="Export response"
                      onClick={() => handleExport(msg)}
                      className="transition hover:text-sky-300"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      aria-label="Escalate to human expert"
                      title="Escalate to human expert"
                      onClick={() => handleEscalate(msg)}
                      disabled={escalatingMessage === msg.id || !!msg.escalationTicket}
                      className="transition hover:text-amber-300 disabled:opacity-50"
                    >
                      {escalatingMessage === msg.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Headphones className="h-3.5 w-3.5" />
                      )}
                    </button>
                  </div>
                )}
                {msg.escalationTicket && (
                  <p className="mt-2 text-xs text-amber-200">
                    Escalation ticket created: {msg.escalationTicket}
                  </p>
                )}
                {msg.escalationError && (
                  <p className="mt-2 text-xs text-rose-300">
                    {msg.escalationError}
                  </p>
                )}
              </div>

              {msg.sources && msg.sources.length > 0 && (
                <SourcesList sources={msg.sources} />
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-white/50">
              <Loader2 className="h-4 w-4 animate-spin" />
              {progressStep ?? 'Retrieving and synthesizing...'}
            </div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="shrink-0 border-t border-white/10 p-4 md:px-8"
      >
        <div className="mx-auto max-w-3xl space-y-2">
          {/* Image preview */}
          {imagePreview && (
            <div className="relative inline-block">
              <img
                src={imagePreview}
                alt="Selected"
                className="h-20 w-auto rounded-lg border border-white/20 object-cover"
              />
              <button
                type="button"
                onClick={clearImage}
                className="absolute -right-2 -top-2 rounded-full bg-gray-800 p-0.5 text-white/70 hover:text-white"
              >
                <X className="h-3.5 w-3.5" />
              </button>
              <Badge className="absolute bottom-1 left-1 text-[9px] bg-black/70">
                {imageFile?.name?.slice(0, 20)}
              </Badge>
            </div>
          )}

          <div className="flex gap-2">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleImageSelect}
            />

            {/* Image upload button */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              className="h-[52px] w-[52px] shrink-0 rounded-xl border border-white/15 text-white/50 hover:text-white/80"
              title="Upload image for analysis"
            >
              <Camera className="h-5 w-5" />
            </Button>

            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder={
                imageFile
                  ? 'Add context for image analysis (optional)…'
                  : domainMode
                  ? `Ask about ${DOMAINS.find(d => d.id === selectedDomain)?.label ?? 'this domain'}…`
                  : 'Ask about policies, architecture, compliance…'
              }
              className="min-h-[52px] resize-none border-white/15 bg-white/5 text-white placeholder:text-white/40"
              rows={1}
            />
            <Button
              type="submit"
              size="icon"
              disabled={(loading || imageAnalyzing) || (!input.trim() && !imageFile)}
              className="h-[52px] w-[52px] shrink-0 rounded-xl"
            >
              {loading || imageAnalyzing
                ? <Loader2 className="h-5 w-5 animate-spin" />
                : <ArrowUp className="h-5 w-5" />
              }
            </Button>
          </div>

          <p className="text-center text-[10px] text-white/25">
            {imageFile
              ? '📷 Image ready — click Send to analyze with Gemini Vision'
              : domainMode
              ? `🤖 Domain AI: ${DOMAINS.find(d => d.id === selectedDomain)?.label} · Powered by RAG + multi-agent`
              : 'Knowledge base RAG · Source citations included · Escalation available'}
          </p>
        </div>
      </form>
    </div>
  );
}





