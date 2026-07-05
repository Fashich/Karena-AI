import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router';
import {
  Activity,
  Database,
  Gauge,
  Headphones,
  MessageSquare,
  Upload,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { fetchAdminStats, fetchHealth, uploadDocument, type AdminStats } from '@/lib/api';

export default function Admin() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [uploadSeconds, setUploadSeconds] = useState(0);
  const uploadTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [s, h] = await Promise.all([fetchAdminStats(), fetchHealth()]);
      setStats(s);
      setHealth(h);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect to backend');
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadSeconds(0);
    setUploadProgress('Uploading...');

    // Timer for elapsed seconds
    uploadTimerRef.current = setInterval(() => {
      setUploadSeconds(s => s + 1);
    }, 1000);

    try {
      // Upload — backend returns job_id immediately
      const API = import.meta.env.VITE_API_URL || '/api/v1';
      const form = new FormData();
      form.append('file', file);
      if (file.name) form.append('title', file.name);

      const uploadRes = await fetch(`${API}/ingest`, { method: 'POST', body: form });
      if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);
      const { job_id } = await uploadRes.json();

      // Poll progress every 500ms
      let done = false;
      while (!done) {
        await new Promise(r => setTimeout(r, 500));
        const progRes = await fetch(`${API}/ingest/progress/${job_id}`);
        if (!progRes.ok) break;
        const prog = await progRes.json();

        // Update UI
        setUploadProgress(prog.message || 'Processing...');

        if (prog.status === 'done') {
          setUploadProgress(`✅ Indexed ${prog.chunks_indexed} chunks from ${prog.total_pages || '?'} pages!`);
          done = true;
          setTimeout(() => { setUploadProgress(null); setUploading(false); }, 3000);
          await load();
        } else if (prog.status === 'error') {
          setError(prog.error || 'Ingestion failed');
          done = true;
          setUploadProgress(null);
          setUploading(false);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploadProgress(null);
      setUploading(false);
    } finally {
      if (uploadTimerRef.current) clearInterval(uploadTimerRef.current);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <Link to="/" className="font-display text-lg font-medium">
          KARENA AI
        </Link>
        <div className="flex gap-3">
          <Link to="/chat">
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" />
              Chat
            </Button>
          </Link>
          <Button variant="ghost" size="sm" onClick={load}>
            Refresh
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-6 md:p-10">
        <h1 className="font-display mb-2 text-3xl font-medium">Admin Dashboard</h1>
        <p className="mb-8 text-white/60">
          Platform observability, ingestion, and SLA monitoring
        </p>

        {error && (
          <div className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">
            {error}
          </div>
        )}

        <div className="mb-8 grid gap-4 md:grid-cols-4">
          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-normal text-white/70">
                <Database className="h-4 w-4" />
                Vector Index
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">
                {stats?.vector_db.points_count ?? '—'}
              </p>
              <p className="text-xs text-white/50">indexed chunks</p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-normal text-white/70">
                <Activity className="h-4 w-4" />
                SLA Target
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">
                {stats?.sla_targets.uptime ?? '99.9%'}
              </p>
              <p className="text-xs text-white/50">
                p95 &lt; {stats?.sla_targets.p95_latency_ms ?? 1000}ms
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-white/70">
                LLM Provider
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold capitalize">
                {stats?.llm_provider ?? '—'}
              </p>
              <p className="truncate text-xs text-white/50">
                {stats?.embedding_model}
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-normal text-white/70">
                <Gauge className="h-4 w-4" />
                Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">
                {stats?.feedback.satisfaction == null
                  ? '—'
                  : `${Math.round(stats.feedback.satisfaction * 100)}%`}
              </p>
              <p className="text-xs text-white/50">
                {stats?.feedback.total ?? 0} responses captured
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="mb-8 grid gap-4 md:grid-cols-4">
          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-white/70">
                MTTR Reduction
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">
                {stats?.validation_metrics.mttr_reduction_target ?? '30%'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-white/70">
                Discovery Acceleration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">
                {stats?.validation_metrics.knowledge_discovery_acceleration_target ??
                  '40%'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-white/70">
                Maintenance Reduction
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">
                {stats?.validation_metrics.documentation_maintenance_reduction_target ??
                  '25%'}
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-white/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm font-normal text-white/70">
                <Headphones className="h-4 w-4" />
                Human Handoff
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold">
                {stats?.escalation?.open ?? 0}
              </p>
              <p className="text-xs text-white/50">
                {stats?.escalation?.total ?? 0} total tickets
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-8 border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle className="text-base">Demo Readiness</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 text-sm md:grid-cols-5">
              {Object.entries(stats?.demo_readiness ?? {}).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-lg border border-white/10 bg-black/20 p-3"
                >
                  <p className="capitalize text-white/60">
                    {key.replaceAll('_', ' ')}
                  </p>
                  <p className={value ? 'text-emerald-300' : 'text-amber-300'}>
                    {value ? 'Ready' : 'Needs setup'}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="mb-8 border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle className="text-base">Document Ingestion</CardTitle>
          </CardHeader>
          <CardContent>
            <label className="flex cursor-pointer items-center gap-3">
              <Input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleUpload}
                disabled={uploading}
                className="border-white/15 bg-white/5"
              />
              <Upload className="h-5 w-5 text-white/50" />
              {uploading ? (
                <div className="text-left w-full">
                  <div className="text-sm font-medium text-white/80 mb-1">{uploadProgress}</div>
                  <div className="text-xs text-white/40 mb-2">{uploadSeconds}s elapsed</div>
                  <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-500 transition-all duration-500"
                      style={{ width: uploading ? `${Math.min(uploadSeconds * 3, 90)}%` : '100%' }}
                    />
                  </div>
                </div>
              ) : 'Upload PDF, DOCX, or text'}
            </label>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-white/5">
          <CardHeader>
            <CardTitle className="text-base">System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-black/30 p-4 text-xs text-white/70">
              {JSON.stringify(health, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
