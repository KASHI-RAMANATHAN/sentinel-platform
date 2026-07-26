import { ChevronRight, ListFilter, ChevronLeft } from 'lucide-react';
import { useState } from 'react';
import type { Alert, Severity } from '@/types';
import Badge from './Badge';
import { AlertsTableSkeleton, Skeleton } from './Skeleton';

interface AlertsTableProps {
  alerts: Alert[];
  selectedId: string;
  onSelect: (alert: Alert) => void;
  loading?: boolean;
  headerActions?: React.ReactNode;
}

const severityStripe: Record<Severity, string> = {
  critical: 'bg-black dark:bg-white',
  high: 'bg-black/60 dark:bg-white/60',
  medium: 'bg-black/40 dark:bg-white/40',
  low: 'bg-black/20 dark:bg-white/20',
  resolved: 'bg-black/10 dark:bg-white/10',
};

export default function AlertsTable({
  alerts,
  selectedId,
  onSelect,
  loading = false,
  headerActions,
}: AlertsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const totalPages = Math.max(1, Math.ceil(alerts.length / itemsPerPage));
  const paginatedAlerts = alerts.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="overflow-hidden rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black">
      <div className="flex items-center justify-between border-b border-black/10 px-6 py-4 dark:border-white/10">
        <div>
          <h3 className="text-[15px] font-semibold tracking-tight text-black dark:text-white">
            Recent Alerts
          </h3>
          <div className="mt-0.5 text-[10px] font-mono text-black/60 dark:text-white/60 uppercase tracking-wider">
            {loading ? (
              <Skeleton className="h-3 w-40" />
            ) : (
              <span>
                {alerts.length} events in the last 24 hours
              </span>
            )}
          </div>
        </div>
        {headerActions ? headerActions : (
          <button className="inline-flex items-center gap-1.5 rounded-none border border-black bg-transparent px-3 py-1.5 text-xs text-black transition-colors hover:bg-black hover:text-white dark:border-white dark:text-white dark:hover:bg-white dark:hover:text-black">
            <ListFilter className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Filter</span>
          </button>
        )}
      </div>

      {loading ? (
        <AlertsTableSkeleton />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-black/10 text-[10px] uppercase tracking-wider text-black/60 dark:border-white/10 dark:text-white/60 font-mono">
                <th className="px-6 py-3 font-medium">ID</th>
                <th className="px-6 py-3 font-medium">Event</th>
                <th className="px-6 py-3 font-medium">Severity</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Risk</th>
                <th className="px-6 py-3 font-medium">Time</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-black/10 dark:divide-white/10">
              {paginatedAlerts.map((alert) => {
                const isSelected = alert.id === selectedId;
                return (
                  <tr
                    key={alert.id}
                    onClick={() => onSelect(alert)}
                    className={`group cursor-pointer transition-colors ${
                      isSelected ? 'bg-black/5 dark:bg-white/10' : 'hover:bg-black/[0.02] dark:hover:bg-white/[0.02]'
                    }`}
                  >
                    <td className="relative px-6 py-4 font-mono text-xs text-black/60 dark:text-white/60">
                      <span
                        className={`absolute left-0 top-1/2 h-full w-1 -translate-y-1/2 ${severityStripe[alert.severity]} transition-opacity ${
                          isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                        }`}
                      />
                      {alert.id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-black dark:text-white">{alert.title}</div>
                      <div className="mt-0.5 text-xs text-black/60 dark:text-white/60">
                        {alert.category}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="severity" value={alert.severity} />
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="status" value={alert.status} />
                    </td>
                    <td className="px-6 py-4">
                      <RiskBar score={alert.riskScore} />
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-black/60 dark:text-white/60">
                      {isNaN(new Date(alert.timestamp).getTime()) ? alert.timestamp : new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ChevronRight
                        className={`h-4 w-4 transition-all ${
                          isSelected
                            ? 'translate-x-1 text-black dark:text-white'
                            : 'text-black/20 group-hover:translate-x-0.5 group-hover:text-black/60 dark:text-white/20 dark:group-hover:text-white/60'
                        }`}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-black/10 px-6 py-3 dark:border-white/10">
          <div className="text-[10px] font-mono text-black/60 dark:text-white/60">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="inline-flex h-7 w-7 items-center justify-center border border-black/20 bg-transparent text-black transition-colors hover:bg-black/5 disabled:opacity-30 disabled:cursor-not-allowed dark:border-white/20 dark:text-white dark:hover:bg-white/5"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="inline-flex h-7 w-7 items-center justify-center border border-black/20 bg-transparent text-black transition-colors hover:bg-black/5 disabled:opacity-30 disabled:cursor-not-allowed dark:border-white/20 dark:text-white dark:hover:bg-white/5"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function RiskBar({ score }: { score: number }) {
  const color =
    score >= 80
      ? 'bg-black dark:bg-white'
      : score >= 60
        ? 'bg-black/70 dark:bg-white/70'
        : score >= 40
          ? 'bg-black/40 dark:bg-white/40'
          : 'bg-black/20 dark:bg-white/20';
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-none border border-black dark:border-white bg-transparent">
        <div
          className={`h-full transition-all duration-500 ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="font-mono text-xs text-black/60 dark:text-white/60">{score}</span>
    </div>
  );
}
