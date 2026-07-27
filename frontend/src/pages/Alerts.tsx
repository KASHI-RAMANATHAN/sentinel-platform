import { useState, useMemo } from 'react';
import AlertsTable from '@/components/dashboard/AlertsTable';
import AlertDetailsPanel from '@/components/dashboard/AlertDetailsPanel';
import type { Alert } from '@/types';
import { Search } from 'lucide-react';

interface AlertsPageProps {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  onInvestigate: (id: string) => void;
  onResolve: (id: string) => void;
}

export default function Alerts({ alerts, loading, error, onInvestigate, onResolve }: AlertsPageProps) {
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  const filteredAlerts = useMemo(() => {
    let result = [...alerts];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(a => 
        a.id.toLowerCase().includes(q) || 
        a.title.toLowerCase().includes(q) || 
        a.category.toLowerCase().includes(q)
      );
    }

    if (severityFilter !== 'all') {
      result = result.filter(a => a.severity === severityFilter);
    }

    if (statusFilter !== 'all') {
      result = result.filter(a => a.status === statusFilter);
    }

    result.sort((a, b) => {
      return sortOrder === 'desc' ? b.riskScore - a.riskScore : a.riskScore - b.riskScore;
    });

    return result;
  }, [alerts, search, severityFilter, statusFilter, sortOrder]);

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Alerts</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            View and manage all security incidents
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          {error && (
            <div className="mb-4 rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
              {error}
            </div>
          )}
          <AlertsTable
            alerts={filteredAlerts}
            selectedId={selectedAlert?.id ?? ''}
            onSelect={setSelectedAlert}
            loading={loading}
            headerActions={
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search alerts..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="h-8 w-48 rounded-xl border border-black/10 bg-white/80 pl-9 pr-3 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#007AFF]/20"
                  />
                </div>
                <select
                  value={severityFilter}
                  onChange={e => setSeverityFilter(e.target.value)}
                  className="h-8 rounded-xl border border-black/10 bg-white/80 px-2 text-xs text-slate-800 focus:outline-none"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                  className="h-8 rounded-xl border border-black/10 bg-white/80 px-2 text-xs text-slate-800 focus:outline-none"
                >
                  <option value="all">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                </select>
                <button 
                  onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
                  className="h-8 rounded-xl border border-black/10 bg-white/80 px-3 text-xs text-slate-800 hover:bg-white"
                >
                  Sort: {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
                </button>
              </div>
            }
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
