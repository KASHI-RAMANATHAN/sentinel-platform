import { useState, useEffect, useMemo } from 'react';
import { db } from '@/lib/firebase';
import { collection, query, orderBy, onSnapshot } from 'firebase/firestore';
import { Search, Filter, AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';

interface AuditEvent {
  id: string;
  log_id?: string;
  timestamp: string;
  actor: string;
  action: string;
  category: string;
  resource: string;
  status: 'Success' | 'Warning' | 'Critical' | 'Failed';
  details: string;
  alert_id?: string;
  entity_id?: string;
}

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  useEffect(() => {
    const q = query(collection(db, 'audit_logs'), orderBy('timestamp', 'desc'));
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const fetchedLogs: AuditEvent[] = [];
      snapshot.forEach((doc) => {
        // Map old fields to new fields for backward compatibility if any exist
        const data = doc.data();
        fetchedLogs.push({
          id: doc.id,
          log_id: data.log_id || doc.id,
          timestamp: data.timestamp,
          actor: data.actor || data.performed_by || 'System',
          action: data.action,
          category: data.category || 'System',
          resource: data.resource || 'N/A',
          status: data.status || 'Success',
          details: data.details || '',
          alert_id: data.alert_id,
          entity_id: data.entity_id,
        });
      });
      setLogs(fetchedLogs);
      setLoading(false);
    }, (error) => {
      console.error("Error fetching audit logs: ", error);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      const matchesCategory = selectedCategory === 'All' || log.category === selectedCategory;
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = 
        log.action.toLowerCase().includes(searchLower) ||
        log.actor.toLowerCase().includes(searchLower) ||
        (log.alert_id && log.alert_id.toLowerCase().includes(searchLower)) ||
        (log.entity_id && log.entity_id.toLowerCase().includes(searchLower)) ||
        log.details.toLowerCase().includes(searchLower);
        
      return matchesCategory && matchesSearch;
    });
  }, [logs, selectedCategory, searchTerm]);

  const StatusBadge = ({ status }: { status: AuditEvent['status'] }) => {
    const styles = {
      Success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
      Warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
      Critical: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
      Failed: 'bg-slate-500/10 text-slate-500 border-slate-500/20',
    };

    const icons = {
      Success: <CheckCircle className="h-3 w-3 mr-1" />,
      Warning: <AlertCircle className="h-3 w-3 mr-1" />,
      Critical: <XCircle className="h-3 w-3 mr-1" />,
      Failed: <Info className="h-3 w-3 mr-1" />,
    };

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${styles[status] || styles.Success}`}>
        {icons[status] || icons.Success}
        {status}
      </span>
    );
  };

  const categories = ['All', 'System', 'Security', 'Analyst', 'Errors'];

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Audit Log</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Immutable record of all system and user activities
          </p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between bg-white dark:bg-black border border-black/10 dark:border-white/10 p-4 rounded-lg">
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400 mr-2" />
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                selectedCategory === category 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-white/10'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-64">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-400" />
          </div>
          <input
            type="text"
            placeholder="Search action, actor, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-slate-200 dark:border-white/10 rounded-md leading-5 bg-transparent placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-black dark:text-white"
          />
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-black/10 bg-white dark:border-white/10 dark:bg-black shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left whitespace-nowrap">
            <thead>
              <tr className="border-b border-black/10 bg-slate-50 dark:bg-white/5 text-[10px] font-mono uppercase tracking-wider text-black/60 dark:border-white/10 dark:text-white/60">
                <th className="px-6 py-3 font-medium">Timestamp</th>
                <th className="px-6 py-3 font-medium">Actor</th>
                <th className="px-6 py-3 font-medium">Category</th>
                <th className="px-6 py-3 font-medium">Action</th>
                <th className="px-6 py-3 font-medium">Resource</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/10 dark:divide-white/10">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-[10px] font-mono uppercase tracking-wider text-black/40 dark:text-white/40">
                    <div className="flex justify-center items-center gap-2">
                      <div className="h-4 w-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                      Loading audit logs...
                    </div>
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-sm text-black/40 dark:text-white/40">
                    <div className="flex flex-col items-center">
                      <Search className="h-8 w-8 text-slate-300 mb-2" />
                      <p>No audit logs found matching your criteria.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4 font-mono text-xs text-black/60 dark:text-white/60">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 font-medium text-sm text-black dark:text-white">
                      {log.actor}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-800 dark:bg-white/10 dark:text-slate-300">
                        {log.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-black dark:text-white">
                      {log.action}
                    </td>
                    <td className="px-6 py-4 text-sm text-black/80 dark:text-white/80">
                      {log.resource}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={log.status} />
                    </td>
                    <td className="px-6 py-4 text-sm text-black/60 dark:text-white/60 truncate max-w-xs" title={log.details}>
                      {log.details || '-'}
                      {log.alert_id && <span className="ml-2 font-mono text-[10px] text-blue-500">[{log.alert_id}]</span>}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
