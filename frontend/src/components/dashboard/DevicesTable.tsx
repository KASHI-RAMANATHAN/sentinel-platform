import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';

export interface Device {
  id: string;
  type: string;
  user: string;
  riskScore: number;
  status: 'active' | 'inactive' | 'compromised';
  lastSeen: string;
}

interface DevicesTableProps {
  devices: Device[];
}

export default function DevicesTable({ devices }: DevicesTableProps) {
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  
  const filteredDevices = useMemo(() => {
    let result = [...devices];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(d => 
        d.id.toLowerCase().includes(q) || 
        d.user.toLowerCase().includes(q) ||
        d.type.toLowerCase().includes(q)
      );
    }

    if (riskFilter !== 'all') {
      const threshold = parseInt(riskFilter);
      if (threshold === 80) result = result.filter(d => d.riskScore >= 80);
      else if (threshold === 60) result = result.filter(d => d.riskScore >= 60 && d.riskScore < 80);
      else if (threshold === 40) result = result.filter(d => d.riskScore >= 40 && d.riskScore < 60);
      else if (threshold === 0) result = result.filter(d => d.riskScore < 40);
    }

    return result;
  }, [devices, search, riskFilter]);

  return (
    <div className="overflow-hidden rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black mt-6">
      <div className="flex items-center justify-between border-b border-black/10 px-6 py-4 dark:border-white/10">
        <div>
          <h3 className="text-[15px] font-semibold tracking-tight text-black dark:text-white">
            Monitored Devices
          </h3>
          <p className="mt-0.5 text-[10px] font-mono uppercase tracking-wider text-black/60 dark:text-white/60">
            <span>{filteredDevices.length} devices found</span>
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-black/40 dark:text-white/40" />
            <input
              type="text"
              placeholder="Search devices..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="h-8 w-48 rounded-none border border-black/20 bg-transparent pl-9 pr-3 text-xs text-black placeholder:text-black/40 focus:border-black focus:outline-none dark:border-white/20 dark:text-white dark:placeholder:text-white/40 dark:focus:border-white"
            />
          </div>
          <select
            value={riskFilter}
            onChange={e => setRiskFilter(e.target.value)}
            className="h-8 rounded-none border border-black/20 bg-transparent px-2 text-xs text-black focus:border-black focus:outline-none dark:border-white/20 dark:text-white dark:focus:border-white"
          >
            <option value="all">All Risk Levels</option>
            <option value="80">Critical (80+)</option>
            <option value="60">High (60-79)</option>
            <option value="40">Medium (40-59)</option>
            <option value="0">Low (0-39)</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-black/10 text-[10px] uppercase tracking-wider text-black/60 dark:border-white/10 dark:text-white/60 font-mono">
              <th className="px-6 py-3 font-medium">Device ID</th>
              <th className="px-6 py-3 font-medium">Type</th>
              <th className="px-6 py-3 font-medium">User</th>
              <th className="px-6 py-3 font-medium">Risk Score</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Last Seen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/10 dark:divide-white/10">
            {filteredDevices.map(device => (
              <tr key={device.id} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors">
                <td className="px-6 py-4 font-mono text-xs text-black dark:text-white">{device.id}</td>
                <td className="px-6 py-4 text-sm text-black/60 dark:text-white/60">{device.type}</td>
                <td className="px-6 py-4 text-sm text-black dark:text-white">{device.user}</td>
                <td className="px-6 py-4">
                  <RiskBar score={device.riskScore} />
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1.5 rounded-none border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wider ${
                    device.status === 'active' ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black' :
                    device.status === 'inactive' ? 'border-black/20 bg-transparent text-black/40 dark:border-white/20 dark:text-white/40' :
                    'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black'
                  }`}>
                    {device.status}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-[10px] uppercase tracking-wider text-black/60 dark:text-white/60">{device.lastSeen}</td>
              </tr>
            ))}
            {filteredDevices.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-sm text-slate-500">
                  No devices match your criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
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
  const level = score >= 80 ? 'Critical' : score >= 60 ? 'High' : score >= 40 ? 'Medium' : 'Low';
  return (
    <div className="w-32">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-mono text-black dark:text-white">{score}/100</span>
        <span className="text-[10px] font-mono uppercase tracking-wider text-black/60 dark:text-white/60">{level}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden border border-black dark:border-white bg-transparent">
        <div 
          className={`h-full transition-all duration-500 ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
