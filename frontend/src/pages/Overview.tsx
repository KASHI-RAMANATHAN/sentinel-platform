import React, { useRef, useState } from 'react';
import {
  TrendingUp,
  Download,
  Activity,
  PieChart,
  ScanLine,
  Cpu,
  CircleDot,
  Upload,
} from 'lucide-react';
import KpiCard from '@/components/dashboard/KpiCard';
import Panel from '@/components/dashboard/Panel';
import AlertsTable from '@/components/dashboard/AlertsTable';
import AlertDetailsPanel from '@/components/dashboard/AlertDetailsPanel';
import AnomalyLineChart from '@/components/charts/AnomalyLineChart';
import AttackPieChart from '@/components/charts/AttackPieChart';
import StatusDot from '@/components/dashboard/StatusDot';
import {
  KpiCardSkeleton,
  ChartSkeleton,
  PieSkeleton,
} from '@/components/dashboard/Skeleton';
import type { Alert, Kpi } from '@/types';
import { type AnomalyPoint, type AttackType, type DashboardStats } from '@/api/dashboard';
import { UploadAPI } from '@/api/upload';

interface OverviewProps {
  loading: boolean;
  liveStats: DashboardStats | null;
  liveKpis: Kpi[];
  statsError: string | null;
  liveTrend: AnomalyPoint[];
  liveDistribution: AttackType[];
  chartsError: string | null;
  liveAlerts: Alert[];
  alertsError: string | null;
  selectedAlert: Alert | null;
  setSelectedAlert: (alert: Alert | null) => void;
  fetchDashboardData: () => Promise<void>;
  onInvestigate: (id: string) => void;
  onResolve: (id: string) => void;
}

export default function Overview({
  loading,
  liveStats,
  liveKpis,
  statsError,
  liveTrend,
  liveDistribution,
  chartsError,
  liveAlerts,
  alertsError,
  selectedAlert,
  setSelectedAlert,
  fetchDashboardData,
  onInvestigate,
  onResolve
}: OverviewProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMessage(null);
    try {
      const result = await UploadAPI.uploadCsv(file);
      setUploadMessage({
        type: 'success',
        text: result.message
      });
      // Clear the previous baseline so that the new dataset doesn't
      // show wildly misleading +/- % deltas compared to the old dataset!
      localStorage.removeItem('sentinel_prev_stats');
      await fetchDashboardData();
    } catch (err: any) {
      const detail = err.response?.data?.message || err.response?.data?.detail || err.message || 'Upload failed.';
      setUploadMessage({
        type: 'error',
        text: `Error processing file: ${detail}`
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <>
      {/* Page header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">
              Security Overview
            </h1>
            <StatusDot color="blue" pulse />
          </div>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Real-time monitoring across your infrastructure
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="file"
            accept=".csv"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileUpload}
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 rounded-none border border-black bg-transparent px-4 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black transition-colors hover:bg-black hover:text-white disabled:opacity-50 disabled:cursor-not-allowed dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-black"
          >
            {uploading ? <Activity className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            <span className="hidden sm:inline">{uploading ? 'Processing...' : 'Upload CSV'}</span>
          </button>
          <button className="inline-flex items-center gap-2 rounded-none border border-black bg-transparent px-4 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black transition-colors hover:bg-black hover:text-white dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-black">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      {/* System status strip */}
      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 rounded-none border border-black/10 bg-transparent px-4 py-3 dark:border-white/10">
        <span className="flex items-center gap-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
          <ScanLine className="h-3.5 w-3.5 text-black dark:text-white" />
          Scanning
        </span>
        <span className="flex items-center gap-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
          <Cpu className="h-3.5 w-3.5 text-black dark:text-white" />
          <span className="font-mono">Engine v4.2.1</span>
        </span>
        <span className="flex items-center gap-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
          <CircleDot className="h-3.5 w-3.5 text-black dark:text-white" />
          <span className="font-mono">
            {liveStats?.devices_monitored?.toLocaleString() ?? 0} endpoints
          </span>
        </span>
        <span className="ml-auto flex items-center gap-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
          <StatusDot color="green" pulse />
          <span className="font-mono">
            Last sync: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' })}
          </span>
        </span>
      </div>

      {uploadMessage && (
        <div className={`mt-5 p-4 text-[13px] font-mono border ${uploadMessage.type === 'error' ? 'bg-red-500/10 text-red-600 border-red-500/30 dark:text-red-400 dark:border-red-500/20' : 'bg-emerald-500/10 text-emerald-700 border-emerald-500/30 dark:text-emerald-400 dark:border-emerald-500/20'}`}>
          {uploadMessage.text}
        </div>
      )}

      {/* KPI cards */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statsError ? (
          <div className="col-span-full rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
            {statsError}
          </div>
        ) : loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <KpiCardSkeleton key={i} />
          ))
        ) : (
          liveKpis.map((kpi) => <KpiCard key={kpi.label} kpi={kpi} />)
        )}
      </div>

      {/* Charts */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {chartsError && (
          <div className="col-span-full rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
            {chartsError}
          </div>
        )}
        <div className="lg:col-span-2">
          <Panel
            title="Anomaly Detection Trend"
            subtitle="Anomalous vs. normal traffic events · last 24h"
            icon={<Activity className="h-4 w-4" />}
            action={
              <div className="flex items-center gap-4">
                <LegendDot color="bg-black dark:bg-white" label="Anomalies" />
                <LegendDot color="bg-black/40 dark:bg-white/40" label="Normal" />
              </div>
            }
          >
            {loading ? (
              <ChartSkeleton />
            ) : (
              <AnomalyLineChart data={liveTrend} />
            )}
          </Panel>
        </div>
        <Panel
          title="Attack Distribution"
          subtitle="By attack vector type"
          icon={<PieChart className="h-4 w-4" />}
        >
          {loading ? <PieSkeleton /> : <AttackPieChart data={liveDistribution} />}
        </Panel>
      </div>

      {/* Alerts + details */}
      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          {alertsError && (
            <div className="mb-4 rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
              {alertsError}
            </div>
          )}
          <AlertsTable
            alerts={liveAlerts}
            selectedId={selectedAlert?.id ?? ''}
            onSelect={setSelectedAlert}
            loading={loading}
          />
        </div>
        <div className="xl:col-span-1">
          <AlertDetailsPanel
            alert={selectedAlert}
            loading={loading}
            onClose={() => setSelectedAlert(null)}
            onInvestigate={onInvestigate}
            onResolve={onResolve}
          />
        </div>
      </div>
    </>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
      <span
        className={`h-2 w-2 rounded-none ${color}`}
      />
      {label}
    </span>
  );
}
