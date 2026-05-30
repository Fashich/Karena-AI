import { useCallback, useRef, useState } from 'react';
import { Link } from 'react-router';
import {
  ArrowUp,
  BookOpen,
  Download,
  Headphones,
  Loader2,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  sendChat,
  createEscalation,
  submitFeedback,
  type ChatResponse,
  type SourceCitation,
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
}

export default function Chat() {
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

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setProgressStep('Classifying intent and tenant context');

    try {
      setTimeout(() => setProgressStep('Retrieving dense and lexical matches'), 250);
      setTimeout(() => setProgressStep('Re-ranking sources and assembling citations'), 700);
      setTimeout(() => setProgressStep('Generating grounded answer'), 1100);
      const res: ChatResponse = await sendChat(text, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: res.answer,
          sources: res.sources,
          confidence: res.confidence,
          latency_ms: res.latency_ms,
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
          content: `Error: ${err instanceof Error ? err.message : 'Request failed'}. Ensure the backend is running on port 8000.`,
        },
      ]);
    } finally {
      setLoading(false);
      setProgressStep(null);
    }
  };

  const suggestions = [
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
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <Link to="/" className="font-display text-lg font-medium tracking-tight">
          KARENA AI
        </Link>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
            RAG Active
          </Badge>
          <Link to="/admin">
            <Button variant="ghost" size="sm" className="text-white/70">
              Admin
            </Button>
          </Link>
        </div>
      </header>

      <ScrollArea className="flex-1 px-4 md:px-8">
        <div className="mx-auto max-w-3xl py-8">
          {messages.length === 0 && (
            <div className="mb-12 text-center">
              <h1 className="font-display mb-3 text-3xl font-medium">
                Enterprise Knowledge Assistant
              </h1>
              <p className="mb-8 text-white/60">
                Ask questions across your unified knowledge base. Responses include
                source citations and confidence indicators.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => {
                      setInput(s);
                    }}
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
                <div className="mt-3 space-y-2 text-left">
                  <p className="flex items-center gap-1 text-xs uppercase tracking-wider text-white/40">
                    <BookOpen className="h-3 w-3" />
                    Sources ({msg.sources.length})
                  </p>
                  {msg.sources.map((src) => (
                    <button
                      key={src.id}
                      type="button"
                      onClick={() =>
                        setExpandedSource(
                          expandedSource === src.id ? null : src.id
                        )
                      }
                      className="block w-full rounded-lg border border-white/10 bg-white/5 p-3 text-left text-sm transition hover:border-white/20"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white/90">
                          {src.title}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          {(src.score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      {expandedSource === src.id && (
                        <p className="mt-2 text-white/60">{src.excerpt}</p>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-white/50">
              <Loader2 className="h-4 w-4 animate-spin" />
              {progressStep ?? 'Retrieving and synthesizing...'}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <form
        onSubmit={handleSubmit}
        className="border-t border-white/10 p-4 md:px-8"
      >
        <div className="mx-auto flex max-w-3xl gap-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Ask about policies, architecture, compliance..."
            className="min-h-[52px] resize-none border-white/15 bg-white/5 text-white placeholder:text-white/40"
            rows={1}
          />
          <Button
            type="submit"
            size="icon"
            disabled={loading || !input.trim()}
            className="h-[52px] w-[52px] shrink-0 rounded-xl"
          >
            <ArrowUp className="h-5 w-5" />
          </Button>
        </div>
      </form>
    </div>
  );
}
