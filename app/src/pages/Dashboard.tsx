import { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate } from 'react-router';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  AlertTriangle, ArrowDownRight, ArrowUpRight, Minus,
  Bus, Heart, Leaf, Users, Siren, GraduationCap, Zap,
  Brain, RefreshCw, MessageSquare, ChevronRight, Activity,
  TrendingUp, Bell, Camera, Info, CheckCircle2, Layers,
  Wifi, WifiOff, Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

const API = '/api/v1';

// ─── Backend metric → KPI display mapping ────────────────────
const DOMAIN_METRICS: Record<string, Array<{
  key: string; label: string; unit: string;
  goodDir: 'up' | 'down' | 'stable'; icon: React.ReactNode;
}>> = {
  urban_mobility: [
    { key: 'avg_commute_time_min',     label: 'Avg Commute',      unit: 'min',   goodDir: 'down', icon: <Bus className="h-4 w-4" /> },
    { key: 'public_transit_usage_pct', label: 'Transit Usage',    unit: '%',     goodDir: 'up',   icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'traffic_congestion_index', label: 'Congestion Index', unit: '/100',  goodDir: 'down', icon: <Activity className="h-4 w-4" /> },
    { key: 'road_incident_count',      label: 'Road Incidents',   unit: 'today', goodDir: 'down', icon: <AlertTriangle className="h-4 w-4" /> },
  ],
  healthcare: [
    { key: 'bed_occupancy_pct',         label: 'Bed Occupancy',   unit: '%',   goodDir: 'down', icon: <Activity className="h-4 w-4" /> },
    { key: 'avg_wait_time_min',         label: 'ER Wait Time',    unit: 'min', goodDir: 'down', icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'active_cases',              label: 'Active Cases',    unit: '',    goodDir: 'down', icon: <Heart className="h-4 w-4" /> },
    { key: 'vaccination_coverage_pct',  label: 'Vaccination',     unit: '%',   goodDir: 'up',   icon: <CheckCircle2 className="h-4 w-4" /> },
  ],
  environment: [
    { key: 'air_quality_index',    label: 'Air Quality (AQI)', unit: '',     goodDir: 'down', icon: <Leaf className="h-4 w-4" /> },
    { key: 'water_quality_score',  label: 'Water Quality',     unit: '/100', goodDir: 'up',   icon: <Activity className="h-4 w-4" /> },
    { key: 'carbon_emissions_mt',  label: 'CO₂ Emissions',     unit: 'MT',   goodDir: 'down', icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'green_coverage_pct',   label: 'Green Coverage',    unit: '%',    goodDir: 'up',   icon: <Leaf className="h-4 w-4" /> },
  ],
  citizen_services: [
    { key: 'open_requests',        label: 'Open Requests',    unit: '',    goodDir: 'down', icon: <Bell className="h-4 w-4" /> },
    { key: 'avg_resolution_days',  label: 'Avg Resolution',   unit: 'days',goodDir: 'down', icon: <Activity className="h-4 w-4" /> },
    { key: 'satisfaction_score',   label: 'Satisfaction',     unit: '/5',  goodDir: 'up',   icon: <CheckCircle2 className="h-4 w-4" /> },
    { key: 'digital_adoption_pct', label: 'Digital Adoption', unit: '%',   goodDir: 'up',   icon: <TrendingUp className="h-4 w-4" /> },
  ],
  disaster_response: [
    { key: 'active_incidents',       label: 'Active Incidents',    unit: '',       goodDir: 'down', icon: <Siren className="h-4 w-4" /> },
    { key: 'resources_deployed_pct', label: 'Resources Deployed',  unit: '%',      goodDir: 'down', icon: <Activity className="h-4 w-4" /> },
    { key: 'early_warning_alerts',   label: 'Early Warnings',      unit: 'active', goodDir: 'down', icon: <Bell className="h-4 w-4" /> },
    { key: 'recovery_rate_pct',      label: 'Recovery Rate',       unit: '%',      goodDir: 'up',   icon: <CheckCircle2 className="h-4 w-4" /> },
  ],
  education: [
    { key: 'enrolment_rate_pct',      label: 'Enrolment Rate',    unit: '%',    goodDir: 'up',   icon: <GraduationCap className="h-4 w-4" /> },
    { key: 'daily_attendance_pct',    label: 'Daily Attendance',  unit: '%',    goodDir: 'up',   icon: <Activity className="h-4 w-4" /> },
    { key: 'learning_outcome_score',  label: 'Learning Score',    unit: '/100', goodDir: 'up',   icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'facility_utilisation_pct',label: 'Facility Util.',    unit: '%',    goodDir: 'up',   icon: <Layers className="h-4 w-4" /> },
  ],
  energy_utilities: [
    { key: 'grid_load_pct',          label: 'Grid Load',        unit: '%',  goodDir: 'down', icon: <Zap className="h-4 w-4" /> },
    { key: 'renewable_share_pct',    label: 'Renewable Share',  unit: '%',  goodDir: 'up',   icon: <TrendingUp className="h-4 w-4" /> },
    { key: 'power_outages_count',    label: 'Power Outages',    unit: 'active', goodDir: 'down', icon: <AlertTriangle className="h-4 w-4" /> },
    { key: 'water_efficiency_pct',   label: 'Water Efficiency', unit: '%',  goodDir: 'up',   icon: <Activity className="h-4 w-4" /> },
  ],
};

const DOMAINS = [
  { id: 'urban_mobility',    label: 'Urban Mobility',    icon: <Bus className="h-4 w-4" />,           color: '#3B82F6', ring: 'ring-blue-500/40',   bgGlow: 'from-blue-900/20',   chatSuggestion: 'What are the best strategies to reduce peak-hour traffic congestion?' },
  { id: 'healthcare',        label: 'Healthcare',         icon: <Heart className="h-4 w-4" />,          color: '#10B981', ring: 'ring-emerald-500/40', bgGlow: 'from-emerald-900/20',chatSuggestion: 'How can we reduce hospital bed occupancy and improve community health?' },
  { id: 'environment',       label: 'Environment',        icon: <Leaf className="h-4 w-4" />,           color: '#22C55E', ring: 'ring-green-500/40',   bgGlow: 'from-green-900/20',  chatSuggestion: 'What actions can reduce air pollution and improve environmental sustainability?' },
  { id: 'citizen_services',  label: 'Citizen Services',   icon: <Users className="h-4 w-4" />,          color: '#A78BFA', ring: 'ring-purple-500/40',  bgGlow: 'from-purple-900/20', chatSuggestion: 'How can we improve citizen satisfaction and reduce service request resolution times?' },
  { id: 'disaster_response', label: 'Disaster Response',  icon: <Siren className="h-4 w-4" />,          color: '#F87171', ring: 'ring-red-500/40',     bgGlow: 'from-red-900/20',    chatSuggestion: 'What is the best disaster preparedness strategy for flood-prone communities?' },
  { id: 'education',         label: 'Education',          icon: <GraduationCap className="h-4 w-4" />,  color: '#FBBF24', ring: 'ring-amber-500/40',   bgGlow: 'from-amber-900/20',  chatSuggestion: 'What educational interventions improve student attendance and outcomes?' },
  { id: 'energy_utilities',  label: 'Energy & Utilities', icon: <Zap className="h-4 w-4" />,            color: '#FDE047', ring: 'ring-yellow-500/40',  bgGlow: 'from-yellow-900/20', chatSuggestion: 'How can we accelerate renewable energy adoption and improve grid resilience?' },
];

const STATIC_ALERTS: Record<string, Array<{severity:'critical'|'warning'|'info'; message:string; time:string}>> = {
  urban_mobility:    [{ severity:'warning',  message:'MRT Line 2 delay — downstream crowding on East corridor',      time:'18 min ago' }, { severity:'info',    message:'Smart parking zones at 94% capacity in CBD — dynamic pricing active',  time:'1h ago' }],
  healthcare:        [{ severity:'critical', message:'Hospital B ICU at 91% — ambulance diversion protocol triggered', time:'5 min ago'  }, { severity:'warning', message:'Dengue cluster (n=7) detected in Sector 4 — vector control deployed',     time:'2h ago' }],
  environment:       [{ severity:'warning',  message:'AQI reached 68 at Station 3 (Industrial Zone) — elevated PM2.5', time:'30 min ago' }, { severity:'info',    message:'River water quality sampling completed — within normal range',            time:'4h ago' }],
  citizen_services:  [{ severity:'warning',  message:'Pothole category SLA breach — 147 requests >5 days unresolved',  time:'2h ago'     }, { severity:'info',    message:'Citizen satisfaction survey results published — score 4.1/5',             time:'6h ago' }],
  disaster_response: [{ severity:'critical', message:'Flash flood warning: Sector 2 riverside — evacuation advisory',  time:'8 min ago'  }, { severity:'warning', message:'Structural fire at Commercial Block 7 — 2 fire units responding',         time:'45 min ago'}],
  education:         [{ severity:'warning',  message:'3 schools below 75% attendance — social worker outreach activated',time:'1h ago'    }, { severity:'info',    message:'Semester learning outcome report published — district average 78/100',    time:'3h ago' }],
  energy_utilities:  [{ severity:'warning',  message:'Grid load at 85% — demand response activated for Zone 3',         time:'12 min ago' }, { severity:'info',    message:'Solar farm output at record 920 MWh today — battery charging activated',  time:'2h ago' }],
};

const days7 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
function randSeries(base: number, std: number, drift = 0) {
  return days7.map((day, i) => ({ day, value: Math.max(0, +(base + drift * i + (Math.random() - 0.5) * std).toFixed(1)) }));
}

// ─── Custom tooltip ───────────────────────────────────────────
const DarkTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/20 bg-gray-950/95 p-3 text-xs shadow-xl">
      <p className="mb-1 font-semibold text-white/80">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>{p.name}: <span className="font-mono font-bold">{p.value}</span></p>
      ))}
    </div>
  );
};

// ─── KPI Card ─────────────────────────────────────────────────
function KPICard({ label, value, unit, delta, deltaDir, deltaGood, icon, color, loading }: {
  label: string; value: string; unit: string; delta: string;
  deltaDir: 'up'|'down'|'stable'; deltaGood: boolean; icon: React.ReactNode;
  color: string; loading?: boolean;
}) {
  const DirIcon = deltaDir === 'up' ? ArrowUpRight : deltaDir === 'down' ? ArrowDownRight : Minus;
  const deltaColor = deltaDir === 'stable' ? 'text-white/40' : deltaGood ? 'text-emerald-400' : 'text-rose-400';
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm transition hover:border-white/20">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-white/40">{label}</span>
        <span style={{ color }} className="opacity-70">{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        {loading
          ? <div className="h-8 w-16 animate-pulse rounded bg-white/10" />
          : <span className="font-mono text-2xl font-bold text-white">{value}</span>
        }
        {unit && <span className="mb-0.5 text-sm text-white/50">{unit}</span>}
      </div>
      {!loading && (
        <div className={cn('mt-1 flex items-center gap-0.5 text-xs font-medium', deltaColor)}>
          <DirIcon className="h-3 w-3" />{delta} vs prev
        </div>
      )}
    </div>
  );
}

// ─── Alert item ───────────────────────────────────────────────
function AlertItem({ alert }: { alert: { severity: string; message: string; time: string } }) {
  const cfg = {
    critical: { cls: 'border-red-500/30 bg-red-500/10 text-red-300',    icon: <Siren className="h-3.5 w-3.5 shrink-0" /> },
    warning:  { cls: 'border-amber-500/30 bg-amber-500/10 text-amber-300', icon: <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> },
    info:     { cls: 'border-blue-500/20 bg-blue-500/10 text-blue-300',  icon: <Info className="h-3.5 w-3.5 shrink-0" /> },
  }[alert.severity as 'critical'|'warning'|'info'] ?? { cls: 'border-white/10 bg-white/5 text-white/50', icon: null };
  return (
    <div className={cn('flex items-start gap-2 rounded-lg border px-3 py-2 text-xs', cfg.cls)}>
      {cfg.icon}<div className="flex-1"><p>{alert.message}</p><p className="mt-0.5 opacity-60">{alert.time}</p></div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────
export default function Dashboard() {
  const [activeId, setActiveId] = useState('urban_mobility');
  const navigate = useNavigate();

  // ── Real-time API state ───────────────────────────────────
  const [snapshot, setSnapshot]     = useState<Record<string, Record<string, number>>>({});
  const [prevSnap, setPrevSnap]     = useState<Record<string, Record<string, number>>>({});
  const [apiInsights, setApiInsights] = useState<Array<{title:string;body:string;impact:string}>>([]);
  const [connected, setConnected]   = useState(false);
  const [loadingSnap, setLoadingSnap] = useState(true);
  const [loadingIns, setLoadingIns]   = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [secondsAgo, setSecondsAgo]   = useState(0);
  const chartDataRef = useRef<Record<string, any>>({});

  // Static chart data (generated once per domain on first load)
  const getChartData = useCallback((id: string) => {
    if (!chartDataRef.current[id]) {
      chartDataRef.current[id] = {
        trend: days7.map((day, i) => ({ day, primary: +(60+Math.random()*30).toFixed(1), secondary: +(50+Math.random()*30).toFixed(1) })),
        bars:  ['A','B','C','D','E','F'].map(n => ({ name: n, value: +(20+Math.random()*70).toFixed(0) })),
      };
    }
    return chartDataRef.current[id];
  }, []);

  // ── Fetch snapshot from backend ───────────────────────────
  const fetchSnapshot = useCallback(async () => {
    try {
      const res = await fetch(`${API}/analytics/snapshot`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPrevSnap(prev => Object.keys(snapshot).length ? snapshot : prev);
      setSnapshot(data.snapshot ?? {});
      setConnected(true);
      setLastUpdated(new Date());
      setSecondsAgo(0);
    } catch {
      setConnected(false);
    } finally {
      setLoadingSnap(false);
    }
  }, [snapshot]);

  // ── Fetch insights for active domain ─────────────────────
  const fetchInsights = useCallback(async (domain: string) => {
    setLoadingIns(true);
    try {
      const res = await fetch(`${API}/analytics/insights/${domain}?max_insights=3`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setApiInsights((data.insights ?? []).map((ins: any) => ({
        title: ins.title ?? 'Insight',
        body: ins.body ?? '',
        impact: ins.impact ?? 'medium',
      })));
    } catch {
      setApiInsights([]);
    } finally {
      setLoadingIns(false);
    }
  }, []);

  // ── Mount: fetch + poll every 30s ────────────────────────
  useEffect(() => {
    fetchSnapshot();
    const t = setInterval(fetchSnapshot, 30_000);
    return () => clearInterval(t);
  }, []); // eslint-disable-line

  // ── Seconds-ago counter ───────────────────────────────────
  useEffect(() => {
    const t = setInterval(() => setSecondsAgo(s => s + 1), 1_000);
    return () => clearInterval(t);
  }, [lastUpdated]);

  // ── Fetch insights on domain switch ──────────────────────
  useEffect(() => {
    fetchInsights(activeId);
  }, [activeId]); // eslint-disable-line

  const domain = DOMAINS.find(d => d.id === activeId) ?? DOMAINS[0];
  const domainMetrics = DOMAIN_METRICS[activeId] ?? [];
  const domainSnap = snapshot[activeId] ?? {};
  const domainPrev = prevSnap[activeId] ?? {};
  const chart = getChartData(activeId);

  // Build KPI cards from backend data (or skeleton if loading)
  const kpiCards = domainMetrics.map(m => {
    const val = domainSnap[m.key];
    const prev = domainPrev[m.key];
    const hasVal = val !== undefined;
    const delta = hasVal && prev !== undefined ? (val - prev).toFixed(1) : '—';
    const deltaNum = hasVal && prev !== undefined ? val - prev : 0;
    let dir: 'up'|'down'|'stable' = 'stable';
    if (deltaNum > 0.05) dir = 'up';
    else if (deltaNum < -0.05) dir = 'down';
    const good = dir === 'stable' ? true : (m.goodDir === 'up' ? dir === 'up' : dir === 'down');
    return {
      label: m.label, unit: m.unit, icon: m.icon,
      value: hasVal ? val.toFixed(val < 10 ? 1 : 0) : '—',
      delta: hasVal && prev !== undefined ? `${deltaNum > 0 ? '+' : ''}${delta}` : '—',
      deltaDir: dir, deltaGood: good,
    };
  });

  const handleAskAI = () => navigate('/chat', { state: { prefill: domain.chatSuggestion } });
  const alerts = STATIC_ALERTS[activeId] ?? [];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0a0a0f]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <Link to="/" className="font-display text-base font-semibold tracking-tight">KARENA AI</Link>
            <span className="hidden text-white/30 sm:inline">/</span>
            <span className="hidden text-sm text-white/60 sm:inline">Decision Intelligence</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={cn('hidden items-center gap-1.5 text-xs sm:flex', connected ? 'text-emerald-400' : 'text-rose-400')}>
              {connected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
              {connected ? `Live · ${secondsAgo}s ago` : 'Offline'}
            </span>
            <Button variant="ghost" size="sm" onClick={fetchSnapshot}
              className="h-8 px-2 text-white/60" disabled={loadingSnap}>
              {loadingSnap ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            </Button>
            <Badge variant="outline" className={cn('text-xs border', connected ? 'border-emerald-500/50 text-emerald-400' : 'border-rose-500/50 text-rose-400')}>
              <span className={cn('mr-1.5 inline-block h-1.5 w-1.5 rounded-full', connected ? 'animate-pulse bg-emerald-400' : 'bg-rose-400')} />
              {connected ? 'Connected' : 'Offline'}
            </Badge>
            <Link to="/chat">
              <Button size="sm" variant="outline" className="h-8 border-white/20 text-xs">
                <MessageSquare className="mr-1.5 h-3.5 w-3.5" />Ask AI
              </Button>
            </Link>
            <Link to="/admin"><Button size="sm" variant="ghost" className="h-8 text-xs text-white/60">Admin</Button></Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-screen-xl px-4 py-6 md:px-6">
        {/* Title */}
        <div className="mb-6">
          <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">Community Decision Intelligence</h1>
          <p className="mt-1 text-sm text-white/50">
            Real-time AI insights from backend analytics engine · auto-refresh every 30s
          </p>
        </div>

        {/* Domain tabs */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-1">
          {DOMAINS.map(d => (
            <button key={d.id} type="button" onClick={() => setActiveId(d.id)}
              className={cn(
                'flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all',
                d.id === activeId
                  ? 'border-white/30 bg-white/10 text-white ring-1 ' + d.ring
                  : 'border-white/10 bg-white/[0.03] text-white/50 hover:border-white/20 hover:text-white/80',
              )}
              style={d.id === activeId ? { color: d.color } : {}}>
              {d.icon}{d.label}
            </button>
          ))}
        </div>

        {/* KPI row — REAL from backend */}
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          {kpiCards.map(k => (
            <KPICard key={k.label} {...k} color={domain.color} loading={loadingSnap} />
          ))}
        </div>

        {/* Charts row */}
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-5">
          <div className="col-span-1 rounded-xl border border-white/10 bg-white/[0.03] p-4 lg:col-span-3">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm font-semibold text-white/80">7-Day Trend</p>
              <Badge variant="secondary" className="text-xs">7 days</Badge>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={chart.trend} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={domain.color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={domain.color} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="day" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<DarkTooltip />} />
                <Area type="monotone" dataKey="primary" name="Primary" stroke={domain.color} strokeWidth={2} fill="url(#g1)" />
                <Area type="monotone" dataKey="secondary" name="Secondary" stroke="#94A3B8" strokeWidth={1.5} fill="none" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="col-span-1 rounded-xl border border-white/10 bg-white/[0.03] p-4 lg:col-span-2">
            <p className="mb-4 text-sm font-semibold text-white/80">Distribution by Sub-area</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chart.bars} layout="vertical" margin={{ top: 0, right: 5, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} width={20} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="value" name="Value" fill={domain.color} radius={[0, 4, 4, 0]} fillOpacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Insights + Alerts — REAL insights from backend */}
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="col-span-1 space-y-3 lg:col-span-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-white/40" />
                <p className="text-sm font-semibold text-white/80">AI-Generated Insights</p>
                {connected && <Badge variant="outline" className="border-emerald-500/30 text-emerald-400 text-[10px]">Live from backend</Badge>}
              </div>
              <button type="button" onClick={handleAskAI}
                className="flex items-center gap-1 text-xs text-white/40 hover:text-white/70 transition">
                Ask AI for more <ChevronRight className="h-3 w-3" />
              </button>
            </div>
            <div className="space-y-3">
              {loadingIns
                ? [1, 2, 3].map(i => (
                    <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <div className="mb-2 h-4 w-2/3 animate-pulse rounded bg-white/10" />
                      <div className="h-3 w-full animate-pulse rounded bg-white/5" />
                    </div>
                  ))
                : apiInsights.length > 0
                ? apiInsights.map(ins => (
                    <div key={ins.title} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold text-white/90 leading-tight">{ins.title}</p>
                        <span className={cn(
                          'shrink-0 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider',
                          ins.impact === 'high' ? 'border-rose-500/30 bg-rose-500/5 text-rose-300' :
                          ins.impact === 'medium' ? 'border-amber-500/30 bg-amber-500/5 text-amber-300' :
                          'border-green-500/30 bg-green-500/5 text-green-300'
                        )}>{ins.impact}</span>
                      </div>
                      <p className="text-xs leading-relaxed text-white/55">{ins.body}</p>
                    </div>
                  ))
                : (
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-xs text-white/40">
                      No insights available for this domain. Backend may be unreachable.
                    </div>
                  )
              }
            </div>
          </div>

          <div className="col-span-1 space-y-3">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-white/40" />
              <p className="text-sm font-semibold text-white/80">Live Alerts</p>
            </div>
            <div className="space-y-2">
              {alerts.map(al => <AlertItem key={al.message} alert={al} />)}
            </div>
            <div className={cn('mt-4 rounded-xl border bg-gradient-to-br p-4', domain.bgGlow, 'border-white/10')}>
              <div className="flex items-center gap-2 text-sm font-semibold text-white/90 mb-2">
                <Brain className="h-4 w-4" style={{ color: domain.color }} />
                Ask Domain AI
              </div>
              <p className="text-xs text-white/50 mb-3">Get deeper insights, forecasts, and action plans.</p>
              <Button size="sm" onClick={handleAskAI} className="w-full text-xs"
                style={{ background: domain.color + '22', borderColor: domain.color + '44' }}>
                <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                "{domain.chatSuggestion.slice(0, 38)}…"
              </Button>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white/80 mb-2">
                <Camera className="h-4 w-4 text-white/40" />Image Analysis
              </div>
              <p className="text-xs text-white/40 mb-3">Upload a photo for AI-powered assessment.</p>
              <Link to="/chat">
                <Button size="sm" variant="outline" className="w-full border-white/15 text-xs text-white/60">
                  Open Multimodal Chat →
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Footer stat bar */}
        <div className="rounded-xl border border-white/10 bg-white/[0.02] px-6 py-3">
          <div className="grid grid-cols-2 gap-4 text-xs text-white/40 sm:grid-cols-4">
            <div><span className="font-medium text-white/70">7</span> AI Domains Active</div>
            <div><span className="font-medium text-white/70">RAG</span> + Groq LLaMA</div>
            <div><span className="font-medium text-white/70">30s</span> Auto-refresh</div>
            <div><span className="font-medium text-white/70">{connected ? 'Live' : 'Offline'}</span> Backend Status</div>
          </div>
        </div>
      </main>
    </div>
  );
}
