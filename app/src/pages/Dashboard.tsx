import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import {
  AlertTriangle, ArrowDownRight, ArrowUpRight, Minus,
  Bus, Heart, Leaf, Users, Siren, GraduationCap, Zap,
  Brain, RefreshCw, MessageSquare, ChevronRight, Activity,
  TrendingUp, Bell, Camera, Info, CheckCircle2, Layers,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────

interface KPI {
  label: string;
  value: string;
  unit: string;
  delta: string;
  deltaDir: 'up' | 'down' | 'stable';
  deltaGood: boolean;
  icon: React.ReactNode;
}

interface TrendPoint {
  day: string;
  primary: number;
  secondary?: number;
  primaryLabel: string;
  secondaryLabel?: string;
}

interface BarPoint {
  name: string;
  value: number;
  target?: number;
}

interface Alert {
  severity: 'critical' | 'warning' | 'info';
  message: string;
  time: string;
}

interface Insight {
  title: string;
  body: string;
  impact: 'high' | 'medium' | 'low';
}

interface Domain {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  ring: string;
  bgGlow: string;
  kpis: KPI[];
  trend: TrendPoint[];
  bars: BarPoint[];
  insights: Insight[];
  alerts: Alert[];
  trendTitle: string;
  barTitle: string;
  chatSuggestion: string;
}

// ─── Colour palette ───────────────────────────────────────────
const C = {
  blue:    '#3B82F6',
  emerald: '#10B981',
  green:   '#22C55E',
  purple:  '#A78BFA',
  red:     '#F87171',
  amber:   '#FBBF24',
  yellow:  '#FDE047',
};

// ─── Domain data ─────────────────────────────────────────────
function buildDomains(): Domain[] {
  // Helper: generate pseudo-random array seeded on mount
  const rng = (base: number, std: number, n: number, drift = 0) =>
    Array.from({ length: n }, (_, i) =>
      Math.max(0, +(base + drift * i + (Math.random() - 0.5) * std).toFixed(1))
    );

  const days7 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return [
    // ── Urban Mobility ─────────────────────────────────────
    {
      id: 'urban_mobility',
      label: 'Urban Mobility',
      icon: <Bus className="h-4 w-4" />,
      color: C.blue,
      ring: 'ring-blue-500/40',
      bgGlow: 'from-blue-900/20',
      kpis: [
        { label: 'Avg Commute', value: '34', unit: 'min', delta: '+2 min', deltaDir: 'up', deltaGood: false, icon: <Bus className="h-4 w-4" /> },
        { label: 'Transit Usage', value: '68', unit: '%', delta: '+5%', deltaDir: 'up', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
        { label: 'Congestion Index', value: '72', unit: '/100', delta: '-3pts', deltaDir: 'down', deltaGood: true, icon: <Activity className="h-4 w-4" /> },
        { label: 'Road Incidents', value: '12', unit: 'today', delta: '-4', deltaDir: 'down', deltaGood: true, icon: <AlertTriangle className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(72, 6, 7, -0.4)[i],
        secondary: rng(67, 4, 7, 0.5)[i],
        primaryLabel: 'Congestion',
        secondaryLabel: 'Transit %',
      })),
      bars: ['CBD', 'North', 'South', 'East', 'West', 'Port'].map((name) => ({
        name, value: +(50 + Math.random() * 40).toFixed(0),
        target: 60,
      })),
      trendTitle: '7-Day Congestion vs Transit Usage',
      barTitle: 'Congestion by Zone',
      insights: [
        { title: 'Peak Hour Congestion Alert', body: 'CBD arterials showing 22% above-baseline congestion during 07:30–09:00. Adaptive signal control deployment recommended.', impact: 'high' },
        { title: 'Transit Ridership Milestone', body: 'Public transit mode share reached 68%, best in 3 years. Sustain current service frequency to retain commuters.', impact: 'medium' },
        { title: 'EV Fleet Expansion Opportunity', body: 'Municipal fleet electrification at 41%. Accelerating to 60% by Q4 saves est. 1,200 MT CO₂/year.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'warning', message: 'MRT Line 2 delay — downstream crowding on East corridor buses', time: '18 min ago' },
        { severity: 'info', message: 'Smart parking zones at 94% capacity in CBD — dynamic pricing active', time: '1h ago' },
      ],
      chatSuggestion: 'What are the best strategies to reduce peak-hour traffic congestion in our city?',
    },

    // ── Healthcare ─────────────────────────────────────────
    {
      id: 'healthcare',
      label: 'Healthcare',
      icon: <Heart className="h-4 w-4" />,
      color: C.emerald,
      ring: 'ring-emerald-500/40',
      bgGlow: 'from-emerald-900/20',
      kpis: [
        { label: 'Bed Occupancy', value: '78', unit: '%', delta: '+3%', deltaDir: 'up', deltaGood: false, icon: <Activity className="h-4 w-4" /> },
        { label: 'ER Wait Time', value: '42', unit: 'min', delta: '-8 min', deltaDir: 'down', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
        { label: 'Active Cases', value: '234', unit: '', delta: '-12', deltaDir: 'down', deltaGood: true, icon: <Heart className="h-4 w-4" /> },
        { label: 'Vaccination', value: '84', unit: '%', delta: '+2%', deltaDir: 'up', deltaGood: true, icon: <CheckCircle2 className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(78, 3, 7, 0.2)[i],
        secondary: rng(42, 5, 7, -0.5)[i],
        primaryLabel: 'Occupancy %',
        secondaryLabel: 'Wait (min)',
      })),
      bars: ['Hospital A', 'Hospital B', 'Clinic C', 'Clinic D', 'Puskesmas E', 'Puskesmas F'].map((name) => ({
        name, value: +(60 + Math.random() * 30).toFixed(0), target: 85,
      })),
      trendTitle: '7-Day Bed Occupancy vs ER Wait Time',
      barTitle: 'Occupancy by Facility',
      insights: [
        { title: 'Bed Capacity Warning', body: 'Three hospitals reporting >82% occupancy. Recommend activating surge protocol and expediting discharge planning.', impact: 'high' },
        { title: 'Vaccination Momentum', body: 'Coverage increased 2% this week. Focused outreach in District 5 and 9 needed to close the 16% gap.', impact: 'medium' },
        { title: 'Mental Health Demand Rising', body: 'Community mental health referrals +18% QoQ. Mobile counselling units deployment can address access barriers.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'critical', message: 'Hospital B ICU at 91% — ambulance diversion protocol triggered', time: '5 min ago' },
        { severity: 'warning', message: 'Dengue cluster (n=7) detected in Sector 4 — vector control deployed', time: '2h ago' },
      ],
      chatSuggestion: 'How can we reduce hospital bed occupancy and improve community health outcomes?',
    },

    // ── Environment ────────────────────────────────────────
    {
      id: 'environment',
      label: 'Environment',
      icon: <Leaf className="h-4 w-4" />,
      color: C.green,
      ring: 'ring-green-500/40',
      bgGlow: 'from-green-900/20',
      kpis: [
        { label: 'Air Quality (AQI)', value: '52', unit: '', delta: '+3', deltaDir: 'up', deltaGood: false, icon: <Leaf className="h-4 w-4" /> },
        { label: 'Water Quality', value: '94', unit: '/100', delta: '-1', deltaDir: 'down', deltaGood: false, icon: <Activity className="h-4 w-4" /> },
        { label: 'CO₂ Emissions', value: '1,240', unit: 'MT', delta: '-45 MT', deltaDir: 'down', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
        { label: 'Green Coverage', value: '31', unit: '%', delta: '↔ stable', deltaDir: 'stable', deltaGood: true, icon: <Leaf className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(52, 7, 7, 0.5)[i],
        secondary: rng(94, 2, 7, -0.1)[i],
        primaryLabel: 'AQI',
        secondaryLabel: 'Water Score',
      })),
      bars: ['Transport', 'Industry', 'Agriculture', 'Residential', 'Waste', 'Other'].map((name) => ({
        name, value: +(10 + Math.random() * 40).toFixed(0),
      })),
      trendTitle: '7-Day AQI vs Water Quality',
      barTitle: 'CO₂ by Emission Source',
      insights: [
        { title: 'AQI Entering Moderate Range', body: 'PM2.5 levels trending upward (52 AQI). Sensitive populations should limit outdoor exposure. Source: traffic + industrial.', impact: 'high' },
        { title: 'Carbon Reduction On-Track', body: 'Monthly CO₂ down 3.5% vs baseline — ahead of annual target. Continue EV fleet transition and renewable procurement.', impact: 'medium' },
        { title: 'Water Quality Monitoring', body: 'Downstream sampling shows trace contaminants in Sector 7. Expanded IoT sensor deployment recommended within 72h.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'warning', message: 'AQI reached 68 at Station 3 (Industrial Zone) — elevated PM2.5', time: '30 min ago' },
        { severity: 'info', message: 'River water quality sampling completed — results within normal range', time: '4h ago' },
      ],
      chatSuggestion: 'What actions can reduce air pollution and improve environmental sustainability in urban areas?',
    },

    // ── Citizen Services ────────────────────────────────────
    {
      id: 'citizen_services',
      label: 'Citizen Services',
      icon: <Users className="h-4 w-4" />,
      color: C.purple,
      ring: 'ring-purple-500/40',
      bgGlow: 'from-purple-900/20',
      kpis: [
        { label: 'Open Requests', value: '1,847', unit: '', delta: '+123', deltaDir: 'up', deltaGood: false, icon: <Bell className="h-4 w-4" /> },
        { label: 'Avg Resolution', value: '3.2', unit: 'days', delta: '-0.8d', deltaDir: 'down', deltaGood: true, icon: <Activity className="h-4 w-4" /> },
        { label: 'Satisfaction', value: '4.1', unit: '/5', delta: '+0.2', deltaDir: 'up', deltaGood: true, icon: <CheckCircle2 className="h-4 w-4" /> },
        { label: 'Digital Adoption', value: '67', unit: '%', delta: '+4%', deltaDir: 'up', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(1800, 120, 7, 20)[i],
        secondary: rng(3.2, 0.4, 7, -0.08)[i],
        primaryLabel: 'Open Requests',
        secondaryLabel: 'Resolution (days)',
      })),
      bars: ['Infrastructure', 'Sanitation', 'Permits', 'Safety', 'Parks', 'Other'].map((name) => ({
        name, value: +(50 + Math.random() * 300).toFixed(0),
      })),
      trendTitle: '7-Day Request Volume vs Resolution Time',
      barTitle: 'Requests by Category',
      insights: [
        { title: 'Service Backlog Growing', body: 'Infrastructure complaints +7% WoW. Automated triage and proactive status notifications can reduce call volume 30%.', impact: 'high' },
        { title: 'Digital Adoption Milestone', body: '67% digital adoption reducing counter queues. Onboarding campaign for remaining 33% offline users recommended.', impact: 'medium' },
        { title: 'AI Chatbot Readiness', body: 'Top 3 request categories (potholes, waste, permits) are rule-based and suitable for 24/7 AI first-response automation.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'warning', message: 'Pothole category SLA breach — 147 requests >5 days unresolved', time: '2h ago' },
        { severity: 'info', message: 'Citizen satisfaction survey results published — score 4.1/5', time: '6h ago' },
      ],
      chatSuggestion: 'How can we improve citizen satisfaction and reduce service request resolution times?',
    },

    // ── Disaster Response ───────────────────────────────────
    {
      id: 'disaster_response',
      label: 'Disaster Response',
      icon: <Siren className="h-4 w-4" />,
      color: C.red,
      ring: 'ring-red-500/40',
      bgGlow: 'from-red-900/20',
      kpis: [
        { label: 'Active Incidents', value: '3', unit: '', delta: '+1', deltaDir: 'up', deltaGood: false, icon: <Siren className="h-4 w-4" /> },
        { label: 'Resources Deployed', value: '47', unit: '%', delta: '-5%', deltaDir: 'down', deltaGood: true, icon: <Activity className="h-4 w-4" /> },
        { label: 'Early Warnings', value: '2', unit: 'active', delta: '↔ stable', deltaDir: 'stable', deltaGood: true, icon: <Bell className="h-4 w-4" /> },
        { label: 'Recovery Rate', value: '89', unit: '%', delta: '+3%', deltaDir: 'up', deltaGood: true, icon: <CheckCircle2 className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(3, 1.5, 7, 0.1)[i],
        secondary: rng(89, 4, 7, 0.3)[i],
        primaryLabel: 'Active Incidents',
        secondaryLabel: 'Recovery %',
      })),
      bars: ['Flood', 'Fire', 'Medical', 'Structure', 'Chemical', 'Other'].map((name) => ({
        name, value: +(2 + Math.random() * 8).toFixed(0),
      })),
      trendTitle: '7-Day Incidents vs Recovery Rate',
      barTitle: 'Incidents by Type (30 days)',
      insights: [
        { title: 'Monsoon Flood Risk Elevated', body: 'Hydrological models predict 65% probability of flash flooding in riverside zones within 72h. Pre-position resources now.', impact: 'high' },
        { title: 'Early Warning System Active', body: '2 active meteorological alerts. Multi-channel broadcast (SMS, radio, app) dissemination is functioning correctly.', impact: 'medium' },
        { title: 'Community Resilience Score', body: 'Volunteer network readiness at 76%. Training 200 additional community first responders closes the gap to target.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'critical', message: 'Flash flood warning: Sector 2 riverside — evacuation advisory issued', time: '8 min ago' },
        { severity: 'warning', message: 'Structural fire at Commercial Block 7 — 2 fire units responding', time: '45 min ago' },
      ],
      chatSuggestion: 'What is the best disaster preparedness strategy for flood-prone communities?',
    },

    // ── Education ───────────────────────────────────────────
    {
      id: 'education',
      label: 'Education',
      icon: <GraduationCap className="h-4 w-4" />,
      color: C.amber,
      ring: 'ring-amber-500/40',
      bgGlow: 'from-amber-900/20',
      kpis: [
        { label: 'Enrolment Rate', value: '94', unit: '%', delta: '+1%', deltaDir: 'up', deltaGood: true, icon: <GraduationCap className="h-4 w-4" /> },
        { label: 'Daily Attendance', value: '87', unit: '%', delta: '-2%', deltaDir: 'down', deltaGood: false, icon: <Activity className="h-4 w-4" /> },
        { label: 'Learning Score', value: '78', unit: '/100', delta: '+4pts', deltaDir: 'up', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
        { label: 'Facility Utilisation', value: '71', unit: '%', delta: '-3%', deltaDir: 'down', deltaGood: false, icon: <Layers className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(87, 3, 7, -0.15)[i],
        secondary: rng(78, 4, 7, 0.3)[i],
        primaryLabel: 'Attendance %',
        secondaryLabel: 'Score',
      })),
      bars: ['Primary', 'Secondary', 'Vocational', 'University', 'Adult Ed'].map((name) => ({
        name, value: +(70 + Math.random() * 25).toFixed(0), target: 90,
      })),
      trendTitle: '7-Day Attendance vs Learning Score',
      barTitle: 'Enrolment Rate by Level',
      insights: [
        { title: 'Attendance Intervention Needed', body: '4 schools below 80% attendance threshold. Correlation with economic stress signals need for conditional support programmes.', impact: 'high' },
        { title: 'Blended Learning Impact', body: 'Learning scores improved +4pts in districts with blended learning pilots. Scale to all 47 schools by next semester.', impact: 'medium' },
        { title: 'STEM Gap Analysis', body: 'Vocational STEM stream showing 12% lower outcomes. Targeted resource allocation and industry mentorship can close gap.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'warning', message: '3 schools below 75% attendance — social worker outreach activated', time: '1h ago' },
        { severity: 'info', message: 'Semester learning outcome report published — district average 78/100', time: '3h ago' },
      ],
      chatSuggestion: 'What educational interventions are most effective for improving student attendance and outcomes?',
    },

    // ── Energy & Utilities ──────────────────────────────────
    {
      id: 'energy_utilities',
      label: 'Energy & Utilities',
      icon: <Zap className="h-4 w-4" />,
      color: C.yellow,
      ring: 'ring-yellow-500/40',
      bgGlow: 'from-yellow-900/20',
      kpis: [
        { label: 'Grid Load', value: '82', unit: '%', delta: '+5%', deltaDir: 'up', deltaGood: false, icon: <Zap className="h-4 w-4" /> },
        { label: 'Renewable Share', value: '34', unit: '%', delta: '+6%', deltaDir: 'up', deltaGood: true, icon: <TrendingUp className="h-4 w-4" /> },
        { label: 'Power Outages', value: '2', unit: 'active', delta: '-1', deltaDir: 'down', deltaGood: true, icon: <AlertTriangle className="h-4 w-4" /> },
        { label: 'Water Efficiency', value: '91', unit: '%', delta: '+1%', deltaDir: 'up', deltaGood: true, icon: <Activity className="h-4 w-4" /> },
      ],
      trend: days7.map((day, i) => ({
        day,
        primary: rng(82, 5, 7, 0.3)[i],
        secondary: rng(34, 2, 7, 0.5)[i],
        primaryLabel: 'Grid Load %',
        secondaryLabel: 'Renewable %',
      })),
      bars: ['Residential', 'Commercial', 'Industrial', 'Public', 'Transport', 'Other'].map((name) => ({
        name, value: +(100 + Math.random() * 400).toFixed(0),
      })),
      trendTitle: '7-Day Grid Load vs Renewable Share',
      barTitle: 'Energy Consumption by Sector (GWh)',
      insights: [
        { title: 'Grid Load Approaching Threshold', body: 'Load at 82% — risk of brownout during afternoon peak. Activate demand response for large commercial consumers immediately.', impact: 'high' },
        { title: 'Renewable Energy Record', body: 'Solar + wind reached 34% share this week, a new record. Battery storage investment needed to capture excess off-peak generation.', impact: 'medium' },
        { title: 'Smart Meter Rollout Impact', body: 'Districts with smart meters show 8% lower peak consumption. Accelerate rollout to remaining 40% of households.', impact: 'medium' },
      ],
      alerts: [
        { severity: 'warning', message: 'Grid load at 85% — demand response programme activated for Zone 3', time: '12 min ago' },
        { severity: 'info', message: 'Solar farm output at record 920 MWh today — battery charging activated', time: '2h ago' },
      ],
      chatSuggestion: 'How can we accelerate renewable energy adoption and improve grid resilience?',
    },
  ];
}

// ─── Custom Chart Tooltip ─────────────────────────────────────
const DarkTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-white/20 bg-gray-950/95 p-3 text-xs shadow-xl">
      <p className="mb-1 font-semibold text-white/80">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-mono font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

// ─── KPI Card ─────────────────────────────────────────────────
function KPICard({ kpi, color }: { kpi: KPI; color: string }) {
  const DirIcon = kpi.deltaDir === 'up'
    ? ArrowUpRight
    : kpi.deltaDir === 'down'
    ? ArrowDownRight
    : Minus;

  const deltaColor = kpi.deltaGood ? 'text-emerald-400' : 'text-rose-400';
  if (kpi.deltaDir === 'stable') {
    // neutral
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm transition hover:border-white/20">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-white/40">{kpi.label}</span>
        <span style={{ color }} className="opacity-70">{kpi.icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className="font-mono text-2xl font-bold text-white">{kpi.value}</span>
        {kpi.unit && <span className="mb-0.5 text-sm text-white/50">{kpi.unit}</span>}
      </div>
      <div className={cn('mt-1 flex items-center gap-0.5 text-xs font-medium', deltaColor)}>
        <DirIcon className="h-3 w-3" />
        {kpi.delta} vs last week
      </div>
    </div>
  );
}

// ─── Alert Item ───────────────────────────────────────────────
function AlertItem({ alert }: { alert: Alert }) {
  const cfg = {
    critical: { cls: 'border-red-500/30 bg-red-500/10 text-red-300', icon: <Siren className="h-3.5 w-3.5 shrink-0" /> },
    warning:  { cls: 'border-amber-500/30 bg-amber-500/10 text-amber-300', icon: <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> },
    info:     { cls: 'border-blue-500/20 bg-blue-500/10 text-blue-300', icon: <Info className="h-3.5 w-3.5 shrink-0" /> },
  }[alert.severity];

  return (
    <div className={cn('flex items-start gap-2 rounded-lg border px-3 py-2 text-xs', cfg.cls)}>
      {cfg.icon}
      <div className="flex-1">
        <p>{alert.message}</p>
        <p className="mt-0.5 opacity-60">{alert.time}</p>
      </div>
    </div>
  );
}

// ─── Insight Card ─────────────────────────────────────────────
function InsightCard({ insight }: { insight: Insight }) {
  const impactCls = {
    high:   'border-rose-500/30 bg-rose-500/5 text-rose-300',
    medium: 'border-amber-500/30 bg-amber-500/5 text-amber-300',
    low:    'border-green-500/30 bg-green-500/5 text-green-300',
  }[insight.impact];

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-white/90 leading-tight">{insight.title}</p>
        <span className={cn('shrink-0 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider', impactCls)}>
          {insight.impact}
        </span>
      </div>
      <p className="text-xs leading-relaxed text-white/55">{insight.body}</p>
    </div>
  );
}

// ─── Main Dashboard Component ─────────────────────────────────
export default function Dashboard() {
  const [domains] = useState<Domain[]>(buildDomains);
  const [activeId, setActiveId] = useState<string>('urban_mobility');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const domain = domains.find((d) => d.id === activeId) ?? domains[0];

  // Simulate live refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => {
      setLastUpdated(new Date());
      setRefreshing(false);
    }, 800);
  }, []);

  const handleAskAI = () => {
    navigate('/chat', { state: { prefill: domain.chatSuggestion } });
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0a0a0f]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <Link to="/" className="font-display text-base font-semibold tracking-tight">
              KARENA AI
            </Link>
            <span className="hidden text-white/30 sm:inline">/</span>
            <span className="hidden text-sm text-white/60 sm:inline">Decision Intelligence</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="hidden text-xs text-white/40 sm:inline">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              className="h-8 px-2 text-white/60"
              disabled={refreshing}
            >
              <RefreshCw className={cn('h-3.5 w-3.5 mr-1', refreshing && 'animate-spin')} />
              Refresh
            </Button>
            <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 text-xs">
              <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              Live
            </Badge>
            <Link to="/chat">
              <Button size="sm" variant="outline" className="h-8 border-white/20 text-xs">
                <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                Ask AI
              </Button>
            </Link>
            <Link to="/admin">
              <Button size="sm" variant="ghost" className="h-8 text-xs text-white/60">
                Admin
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-screen-xl px-4 py-6 md:px-6">

        {/* ── Page title ─────────────────────────────────────── */}
        <div className="mb-6">
          <h1 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
            Community Decision Intelligence
          </h1>
          <p className="mt-1 text-sm text-white/50">
            AI-powered insights across 7 community domains · powered by RAG + Gemini
          </p>
        </div>

        {/* ── Domain tabs ─────────────────────────────────────── */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-1">
          {domains.map((d) => (
            <button
              key={d.id}
              type="button"
              onClick={() => setActiveId(d.id)}
              className={cn(
                'flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all',
                d.id === activeId
                  ? 'border-white/30 bg-white/10 text-white ring-1 ' + d.ring
                  : 'border-white/10 bg-white/[0.03] text-white/50 hover:border-white/20 hover:text-white/80',
              )}
              style={d.id === activeId ? { color: d.color } : {}}
            >
              {d.icon}
              {d.label}
            </button>
          ))}
        </div>

        {/* ── KPI row ─────────────────────────────────────────── */}
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          {domain.kpis.map((kpi) => (
            <KPICard key={kpi.label} kpi={kpi} color={domain.color} />
          ))}
        </div>

        {/* ── Charts row ──────────────────────────────────────── */}
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-5">
          {/* Area chart (60%) */}
          <div className="col-span-1 rounded-xl border border-white/10 bg-white/[0.03] p-4 lg:col-span-3">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm font-semibold text-white/80">{domain.trendTitle}</p>
              <Badge variant="secondary" className="text-xs">7 days</Badge>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={domain.trend} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="grad1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={domain.color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={domain.color} stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="grad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#94A3B8" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#94A3B8" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="day" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<DarkTooltip />} />
                <Area
                  type="monotone"
                  dataKey="primary"
                  name={domain.trend[0]?.primaryLabel ?? 'Primary'}
                  stroke={domain.color}
                  strokeWidth={2}
                  fill="url(#grad1)"
                />
                {domain.trend[0]?.secondary != null && (
                  <Area
                    type="monotone"
                    dataKey="secondary"
                    name={domain.trend[0]?.secondaryLabel ?? 'Secondary'}
                    stroke="#94A3B8"
                    strokeWidth={1.5}
                    fill="url(#grad2)"
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Bar chart (40%) */}
          <div className="col-span-1 rounded-xl border border-white/10 bg-white/[0.03] p-4 lg:col-span-2">
            <div className="mb-4">
              <p className="text-sm font-semibold text-white/80">{domain.barTitle}</p>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={domain.bars} layout="vertical" margin={{ top: 0, right: 5, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} width={80} />
                <Tooltip content={<DarkTooltip />} />
                <Bar dataKey="value" name="Value" fill={domain.color} radius={[0, 4, 4, 0]} fillOpacity={0.8} />
                {domain.bars[0]?.target != null && (
                  <Bar dataKey="target" name="Target" fill="rgba(255,255,255,0.1)" radius={[0, 4, 4, 0]} />
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── Insights + Alerts row ────────────────────────────── */}
        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Insights (2/3) */}
          <div className="col-span-1 space-y-3 lg:col-span-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-white/40" />
                <p className="text-sm font-semibold text-white/80">AI-Generated Insights</p>
              </div>
              <button
                type="button"
                onClick={handleAskAI}
                className="flex items-center gap-1 text-xs text-white/40 hover:text-white/70 transition"
              >
                Ask AI for more
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>
            <div className="space-y-3">
              {domain.insights.map((ins) => (
                <InsightCard key={ins.title} insight={ins} />
              ))}
            </div>
          </div>

          {/* Alerts (1/3) */}
          <div className="col-span-1 space-y-3">
            <div className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-white/40" />
              <p className="text-sm font-semibold text-white/80">Live Alerts</p>
            </div>
            <div className="space-y-2">
              {domain.alerts.map((al) => (
                <AlertItem key={al.message} alert={al} />
              ))}
              {domain.alerts.length === 0 && (
                <div className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/30">
                  No active alerts for this domain.
                </div>
              )}
            </div>

            {/* Quick action CTA */}
            <div className={cn(
              'mt-4 rounded-xl border bg-gradient-to-br p-4',
              domain.bgGlow,
              'border-white/10',
            )}>
              <div className="flex items-center gap-2 text-sm font-semibold text-white/90 mb-2">
                <Brain className="h-4 w-4" style={{ color: domain.color }} />
                Ask Domain AI
              </div>
              <p className="text-xs text-white/50 mb-3">
                Get deeper insights, predictive forecasts, and action plans from the knowledge base.
              </p>
              <Button
                size="sm"
                onClick={handleAskAI}
                className="w-full text-xs"
                style={{ background: domain.color + '22', borderColor: domain.color + '44' }}
              >
                <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                "{domain.chatSuggestion.slice(0, 40)}…"
              </Button>
            </div>

            {/* Multimodal analysis */}
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-white/80 mb-2">
                <Camera className="h-4 w-4 text-white/40" />
                Image Analysis
              </div>
              <p className="text-xs text-white/40 mb-3">
                Upload a photo for AI-powered assessment (infrastructure, environment, incidents).
              </p>
              <Link to="/chat">
                <Button size="sm" variant="outline" className="w-full border-white/15 text-xs text-white/60">
                  Open Multimodal Chat →
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* ── Footer stat bar ─────────────────────────────────── */}
        <div className="rounded-xl border border-white/10 bg-white/[0.02] px-6 py-3">
          <div className="grid grid-cols-2 gap-4 text-xs text-white/40 sm:grid-cols-4">
            <div><span className="font-medium text-white/70">7</span> AI Domains Active</div>
            <div><span className="font-medium text-white/70">RAG</span> + Gemini Powered</div>
            <div><span className="font-medium text-white/70">Google ADK</span> Multi-Agent Ready</div>
            <div><span className="font-medium text-white/70">Real-time</span> Anomaly Detection</div>
          </div>
        </div>
      </main>
    </div>
  );
}
