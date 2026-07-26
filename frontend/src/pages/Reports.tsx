import { Download, FileText } from 'lucide-react';
import KpiCard from '@/components/dashboard/KpiCard';
import Panel from '@/components/dashboard/Panel';
import AnomalyLineChart from '@/components/charts/AnomalyLineChart';
import AttackPieChart from '@/components/charts/AttackPieChart';
import { ChartSkeleton, PieSkeleton, KpiCardSkeleton } from '@/components/dashboard/Skeleton';
import type { Kpi, Alert } from '@/types';
import { type AnomalyPoint, type AttackType, type DashboardStats } from '@/api/dashboard';

interface ReportsProps {
  loading: boolean;
  liveStats: DashboardStats | null;
  liveKpis: Kpi[];
  statsError: string | null;
  liveTrend: AnomalyPoint[];
  liveDistribution: AttackType[];
  chartsError: string | null;
  liveAlerts: Alert[];
}

export default function Reports({
  loading,
  liveStats,
  liveKpis,
  statsError,
  liveTrend,
  liveDistribution,
  chartsError,
  liveAlerts
}: ReportsProps) {

  const exportReport = () => {
    // Basic CSV Generation from liveAlerts
    const headers = ['ID', 'Title', 'Severity', 'Status', 'Category', 'Timestamp', 'Risk Score', 'Source', 'Destination'];
    const rows = liveAlerts.map(a => [
      a.id,
      `"${a.title}"`,
      a.severity,
      a.status,
      a.category,
      a.timestamp,
      a.riskScore,
      a.source,
      a.destination
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(e => e.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `security_report_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Security Reports</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Exportable summaries of your infrastructure's security posture
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={exportReport}
            className="inline-flex items-center gap-2 rounded-none border border-black bg-transparent px-4 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider text-black transition-colors hover:bg-black hover:text-white dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-black"
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export Report (CSV)</span>
          </button>
        </div>
      </div>

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

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {chartsError && (
          <div className="col-span-full rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
            {chartsError}
          </div>
        )}
        <div className="lg:col-span-2">
          <Panel
            title="Attack Trends"
            subtitle="Anomalous vs normal traffic over time"
            icon={<FileText className="h-4 w-4" />}
          >
            {loading ? <ChartSkeleton /> : <AnomalyLineChart data={liveTrend} />}
          </Panel>
        </div>
        <Panel
          title="Threat Distribution"
          subtitle="Breakdown of attack vectors"
          icon={<FileText className="h-4 w-4" />}
        >
          {loading ? <PieSkeleton /> : <AttackPieChart data={liveDistribution} />}
        </Panel>
      </div>

    </>
  );
}
