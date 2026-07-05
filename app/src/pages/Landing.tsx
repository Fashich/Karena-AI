import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import {
  Bus, Heart, Leaf, Users, Siren, GraduationCap, Zap,
  Brain, BarChart3, Shield, ArrowRight, CheckCircle,
  Globe, Database, Cpu, Activity, ChevronRight,
} from 'lucide-react';

const DOMAINS = [
  { icon: Bus,           color: '#3B82F6', label: 'Urban Mobility',    desc: 'Real-time traffic, transit ridership, and commute analytics for smarter city movement.' },
  { icon: Heart,         color: '#10B981', label: 'Healthcare',         desc: 'Hospital capacity, disease surveillance, and vaccination coverage monitoring.' },
  { icon: Leaf,          color: '#22C55E', label: 'Environment',        desc: 'Air quality, carbon emissions, water safety, and climate resilience tracking.' },
  { icon: Users,         color: '#A78BFA', label: 'Citizen Services',   desc: 'Service request management, resolution analytics, and digital adoption metrics.' },
  { icon: Siren,         color: '#F87171', label: 'Disaster Response',  desc: 'Early warning systems, resource deployment, and community recovery dashboards.' },
  { icon: GraduationCap, color: '#FBBF24', label: 'Education',          desc: 'Enrolment, attendance patterns, and learning outcome intelligence across districts.' },
  { icon: Zap,           color: '#FDE047', label: 'Energy & Utilities', desc: 'Grid load, renewable share, and smart utility efficiency optimisation.' },
];

const STEPS = [
  { n: '01', title: 'Ingest Community Data',   desc: 'Connect structured and unstructured data from urban sensors, public services, citizen reports, and government APIs.' },
  { n: '02', title: 'AI Analysis & Retrieval', desc: 'Hybrid RAG pipeline retrieves relevant knowledge. Gemini-powered domain agents analyse patterns and anomalies.' },
  { n: '03', title: 'Actionable Decisions',    desc: 'Domain-specific recommendations, predictive forecasts, and escalation alerts delivered to the right stakeholders.' },
];

const CAPABILITIES = [
  { icon: Brain,    title: 'Multi-Agent Intelligence', desc: '7 specialist AI agents with deep community domain context, orchestrated via Google ADK-ready architecture.' },
  { icon: BarChart3, title: 'Predictive Analytics',   desc: 'Time-series forecasting, anomaly detection, and auto-generated insights with confidence intervals.' },
  { icon: Shield,   title: 'Enterprise Security',      desc: 'PII/DLP protection, PDPA/GDPR compliance, API key lifecycle, audit logs, and OAuth2/OIDC SSO.' },
];

const TECH = ['Gemini 2.0 Flash', 'Google ADK', 'Cloud Run', 'RAG + Qdrant', 'OpenTelemetry', 'Vertex AI'];

const CHECKS = [
  'Hybrid RAG (Dense + BM25)', 'Gemini Vision Multimodal', 'Real-time Anomaly Detection',
  'Predictive Forecasting', 'PII / DLP Protection', 'PDPA & GDPR Compliant',
  'OpenTelemetry Tracing', 'Kubernetes / Cloud Run', 'Prometheus Metrics',
  'Multi-tenant RBAC', 'ADK-ready Agents', 'Source Citations',
];

function useCounter(target: number, duration = 1200) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let cur = 0;
    const step = target / (duration / 16);
    const t = setInterval(() => {
      cur = Math.min(cur + step, target);
      setVal(Math.floor(cur));
      if (cur >= target) clearInterval(t);
    }, 16);
    return () => clearInterval(t);
  }, [target, duration]);
  return val;
}

function LiveMetrics() {
  const [m, setM] = useState({ decisions: 1247, alerts: 3, communities: 28, uptime: 99.9 });
  useEffect(() => {
    const t = setInterval(() => {
      setM(p => ({
        decisions:   p.decisions + Math.floor(Math.random() * 3),
        alerts:      Math.max(1, p.alerts + (Math.random() > 0.85 ? 1 : Math.random() > 0.85 ? -1 : 0)),
        communities: p.communities,
        uptime:      99.9,
      }));
    }, 2500);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-white/40">Live Platform Metrics</span>
        <span className="flex items-center gap-1.5 text-[10px] text-emerald-400">
          <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          Real-time
        </span>
      </div>
      <div className="mb-4 grid grid-cols-2 gap-3">
        {[
          { label: 'AI Decisions Today', value: m.decisions.toLocaleString(), color: 'text-blue-400' },
          { label: 'Active Alerts',       value: String(m.alerts),            color: 'text-amber-400' },
          { label: 'Communities Served',  value: String(m.communities),       color: 'text-emerald-400' },
          { label: 'Platform Uptime',     value: `${m.uptime}%`,             color: 'text-purple-400' },
        ].map(s => (
          <div key={s.label} className="rounded-xl border border-white/8 bg-white/[0.03] p-3">
            <div className={`font-mono text-xl font-bold ${s.color}`}>{s.value}</div>
            <div className="mt-0.5 text-[10px] text-white/40">{s.label}</div>
          </div>
        ))}
      </div>
      {[
        { label: 'Urban Mobility', pct: 72, color: 'bg-blue-500' },
        { label: 'Healthcare',     pct: 85, color: 'bg-emerald-500' },
        { label: 'Environment',    pct: 61, color: 'bg-green-500' },
      ].map(b => (
        <div key={b.label} className="mb-2 flex items-center gap-2">
          <span className="w-28 text-[10px] text-white/40">{b.label}</span>
          <div className="h-1 flex-1 rounded-full bg-white/10">
            <div className={`h-full rounded-full ${b.color}`} style={{ width: `${b.pct}%` }} />
          </div>
          <span className="w-8 text-right font-mono text-[10px] text-white/50">{b.pct}</span>
        </div>
      ))}
    </div>
  );
}

export default function Landing() {
  const domains = useCounter(7);
  const queries = useCounter(98);
  const uptime  = useCounter(99);

  return (
    <div className="min-h-screen bg-[#050c18] font-sans text-white">

      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/8 bg-[#050c18]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold tracking-tight">KARENA AI</span>
            <span className="rounded-full border border-blue-500/40 bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-blue-400">Beta</span>
          </div>
          <div className="hidden items-center gap-6 md:flex">
            {['Platform', 'Intelligence', 'Security'].map(l => (
              <a key={l} href={`#${l.toLowerCase()}`} className="text-sm text-white/50 transition hover:text-white">{l}</a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="hidden rounded-lg border border-white/15 px-4 py-2 text-sm text-white/70 transition hover:border-white/30 hover:text-white md:block">
              Dashboard
            </Link>
            <Link to="/chat" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500">
              Try AI Assistant →
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0"
          style={{ backgroundImage: 'linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />
        <div className="pointer-events-none absolute left-1/4 top-0 h-96 w-96 -translate-x-1/2 rounded-full bg-blue-600/10 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-6 py-20 md:py-28">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
                <span className="text-xs font-medium text-blue-300">APAC Generative AI Hackathon 2026 · Hack2Skill</span>
              </div>

              <h1 className="mb-6 text-4xl font-extrabold leading-tight tracking-tight md:text-5xl xl:text-6xl">
                Community{' '}
                <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  Decision Intelligence
                </span>{' '}
                Platform
              </h1>

              <p className="mb-8 max-w-lg text-base leading-relaxed text-white/60 md:text-lg">
                AI-powered insights across 7 community domains — urban mobility, healthcare, environment,
                citizen services, disaster response, education, and energy. Powered by RAG + Gemini for APAC city stakeholders.
              </p>

              <div className="flex flex-wrap gap-3">
                <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500">
                  <BarChart3 className="h-4 w-4" /> Open Dashboard
                </Link>
                <Link to="/chat" className="inline-flex items-center gap-2 rounded-xl border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:border-white/40 hover:bg-white/5">
                  <Brain className="h-4 w-4" /> Try AI Assistant
                </Link>
              </div>

              <div className="mt-10 flex flex-wrap gap-6">
                {[
                  { val: `${domains}`, unit: 'AI Domains' },
                  { val: `${queries}%`, unit: 'RAG Accuracy' },
                  { val: `${uptime}.9%`, unit: 'Uptime' },
                  { val: 'Gemini', unit: 'Vision + Language' },
                ].map(s => (
                  <div key={s.unit}>
                    <div className="font-mono text-2xl font-bold">{s.val}</div>
                    <div className="text-xs text-white/40">{s.unit}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="hidden lg:block"><LiveMetrics /></div>
          </div>
        </div>
      </section>

      {/* Tech bar */}
      <section className="border-y border-white/8 bg-white/[0.02]">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <div className="flex flex-wrap items-center justify-center gap-3">
            <span className="mr-2 text-xs text-white/30">Built on</span>
            {TECH.map(t => (
              <span key={t} className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-white/60">{t}</span>
            ))}
          </div>
        </div>
      </section>

      {/* Domains */}
      <section id="platform" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mb-12 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">7 Community Domains</p>
          <h2 className="mb-4 text-3xl font-extrabold tracking-tight md:text-4xl">Intelligence Across Every Domain</h2>
          <p className="mx-auto max-w-2xl text-white/50">
            Specialist AI agents with deep domain context — automatically routing queries to the right expert
            and generating actionable, evidence-based recommendations.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {DOMAINS.map(d => {
            const Icon = d.icon;
            return (
              <Link to="/dashboard" key={d.label}
                className="group rounded-2xl border border-white/8 bg-white/[0.03] p-5 transition hover:border-white/20 hover:bg-white/[0.06]">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-white/10"
                  style={{ backgroundColor: d.color + '18' }}>
                  <Icon className="h-5 w-5" style={{ color: d.color }} />
                </div>
                <div className="mb-1.5 font-semibold">{d.label}</div>
                <div className="text-xs leading-relaxed text-white/45">{d.desc}</div>
                <div className="mt-3 flex items-center gap-1 text-xs font-medium" style={{ color: d.color }}>
                  View insights <ChevronRight className="h-3 w-3" />
                </div>
              </Link>
            );
          })}
          <Link to="/chat"
            className="flex flex-col items-center justify-center rounded-2xl border border-blue-500/30 bg-blue-500/5 p-5 text-center transition hover:bg-blue-500/10">
            <Brain className="mb-3 h-8 w-8 text-blue-400" />
            <div className="mb-1 font-semibold text-blue-300">Ask Domain AI</div>
            <div className="text-xs text-blue-400/60">Query any domain in natural language</div>
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section id="intelligence" className="border-y border-white/8 bg-white/[0.015]">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="mb-12 text-center">
            <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">How It Works</p>
            <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">From Raw Data to Confident Decisions</h2>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {STEPS.map(s => (
              <div key={s.n} className="rounded-2xl border border-white/8 bg-white/[0.03] p-7">
                <div className="mb-4 font-mono text-4xl font-bold text-white/10">{s.n}</div>
                <div className="mb-2 text-lg font-bold">{s.title}</div>
                <div className="text-sm leading-relaxed text-white/50">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="mb-12 text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">Capabilities</p>
          <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">Enterprise-Grade AI Infrastructure</h2>
        </div>
        <div className="mb-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          {CAPABILITIES.map(c => {
            const Icon = c.icon;
            return (
              <div key={c.title} className="rounded-2xl border border-white/8 bg-white/[0.03] p-7">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl border border-blue-500/30 bg-blue-500/10">
                  <Icon className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="mb-2 text-lg font-bold">{c.title}</h3>
                <p className="text-sm leading-relaxed text-white/50">{c.desc}</p>
              </div>
            );
          })}
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {CHECKS.map(f => (
            <div key={f} className="flex items-start gap-2 text-xs text-white/50">
              <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
              {f}
            </div>
          ))}
        </div>
      </section>

      {/* Google Cloud */}
      <section id="security" className="border-y border-white/8 bg-white/[0.015]">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid grid-cols-1 gap-10 md:grid-cols-2 md:items-center">
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">Google Cloud Ecosystem</p>
              <h2 className="mb-4 text-3xl font-extrabold tracking-tight">Built for the APAC Cloud</h2>
              <p className="mb-6 leading-relaxed text-white/50">
                Designed around the Google Cloud AI stack — Gemini LLMs, Vertex AI, Cloud Run, and Agent Development Kit —
                with upgrade paths from development to production at scale.
              </p>
              <div className="flex flex-wrap gap-2">
                {[
                  { icon: Globe, label: 'Cloud Run' }, { icon: Database, label: 'AlloyDB' },
                  { icon: Cpu, label: 'Vertex AI' },   { icon: Activity, label: 'Gemini 2.0' },
                ].map(b => {
                  const Icon = b.icon;
                  return (
                    <div key={b.label} className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/70">
                      <Icon className="h-4 w-4 text-blue-400" />{b.label}
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'LLM & Vision',    val: 'Gemini 2.0 Flash', sub: 'Text + Image analysis' },
                { label: 'Agent Framework', val: 'Google ADK',       sub: '7 specialist agents'   },
                { label: 'Vector Search',   val: 'Qdrant HNSW',      sub: 'Hybrid dense + BM25'   },
                { label: 'Deployment',      val: 'Cloud Run + K8s',  sub: 'Terraform provisioned' },
              ].map(s => (
                <div key={s.label} className="rounded-xl border border-white/8 bg-white/[0.03] p-4">
                  <div className="mb-1 text-[10px] uppercase tracking-wider text-white/30">{s.label}</div>
                  <div className="font-semibold">{s.val}</div>
                  <div className="text-xs text-white/40">{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="relative overflow-hidden rounded-3xl border border-blue-500/20 bg-gradient-to-br from-blue-600/15 via-blue-800/10 to-transparent p-10 text-center md:p-16">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/50 to-transparent" />
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-blue-400">Decision Intelligence, Live</p>
          <h2 className="mb-4 text-3xl font-extrabold tracking-tight md:text-4xl">Start Making Better Community Decisions</h2>
          <p className="mx-auto mb-8 max-w-xl text-white/55">
            Explore the live dashboard, query the AI assistant, or analyze images of community infrastructure —
            all powered by Gemini and RAG.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/dashboard" className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/30 transition hover:bg-blue-500">
              <BarChart3 className="h-4 w-4" /> Open Dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/chat" className="inline-flex items-center gap-2 rounded-xl border border-white/20 px-8 py-3.5 text-sm font-semibold transition hover:border-white/40 hover:bg-white/5">
              <Brain className="h-4 w-4" /> Try AI Assistant
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/8 bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
            <div>
              <div className="mb-1 font-mono text-base font-bold">KARENA AI</div>
              <div className="text-sm text-white/40">Community Decision Intelligence · APAC Generative AI Hackathon 2026</div>
            </div>
            <div className="flex flex-wrap gap-6 text-sm text-white/40">
              <Link to="/dashboard" className="transition hover:text-white">Dashboard</Link>
              <Link to="/chat"      className="transition hover:text-white">AI Assistant</Link>
              <Link to="/admin"     className="transition hover:text-white">Admin</Link>
              <a href="http://localhost:8080/docs" target="_blank" rel="noreferrer" className="transition hover:text-white">API Docs</a>
            </div>
          </div>
          <div className="mt-8 border-t border-white/8 pt-6 text-xs text-white/25">
            Built with Gemini · RAG · Google ADK · FastAPI · React 19 · Qdrant
          </div>
        </div>
      </footer>
    </div>
  );
}
