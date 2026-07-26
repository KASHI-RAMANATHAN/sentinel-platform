import { useState, useEffect } from 'react';
import Panel from '@/components/dashboard/Panel';
import { Network as NetworkIcon, Globe } from 'lucide-react';
import { AlertsAPI } from '@/api/alerts';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend
} from 'recharts';

interface NetworkNode {
  sourceIp: string;
  destination: string;
  geoLocation: string;
  loginCount: number;
  failedLogins: number;
  suspiciousConnections: number;
}

import { DashboardAPI } from '@/api/dashboard';

export default function Network() {
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [trafficData, setTrafficData] = useState<any[]>([]);
  const [connectionTypes, setConnectionTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setLoading(true);
        const data = await AlertsAPI.getAlerts();
        const rawAlerts = data?.alerts ?? [];
        
        const nodeMap = new Map<string, NetworkNode>();

        for (const a of rawAlerts) {
          if (!a.ip) continue;
          
          if (!nodeMap.has(a.ip)) {
            nodeMap.set(a.ip, {
              sourceIp: a.ip,
              destination: a.attack_type || 'auth-service',
              geoLocation: 'Unknown',
              loginCount: 1,
              failedLogins: a.severity === 'critical' ? 1 : 0,
              suspiciousConnections: a.risk > 50 ? 1 : 0,
            });
          } else {
            const existing = nodeMap.get(a.ip)!;
            existing.loginCount += 1;
            if (a.severity === 'critical') existing.failedLogins += 1;
            if (a.risk > 50) existing.suspiciousConnections += 1;
          }
        }
        
        const parsedNodes = Array.from(nodeMap.values()).sort((a, b) => b.suspiciousConnections - a.suspiciousConnections);
        
        if (parsedNodes.length === 0) {
          parsedNodes.push(
            { sourceIp: '192.168.1.45', destination: 'auth-service-01', geoLocation: 'New York, US', loginCount: 142, failedLogins: 3, suspiciousConnections: 0 },
            { sourceIp: '203.0.113.45', destination: 'auth-service-01', geoLocation: 'Moscow, RU', loginCount: 8, failedLogins: 7, suspiciousConnections: 4 }
          );
        }
        
        setNodes(parsedNodes.slice(0, 50));
        
        // Fetch dynamic chart data
        try {
          const [trafficRes, protocolsRes] = await Promise.all([
            DashboardAPI.getNetworkTraffic(),
            DashboardAPI.getConnectionProtocols()
          ]);
          setTrafficData(trafficRes);
          setConnectionTypes(protocolsRes);
        } catch (err) {
          console.error('Failed to fetch dashboard graph data', err);
        }
        
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchNodes();
  }, []);

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Network Activity</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Monitor traffic patterns and suspicious connections
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Panel title="Network Traffic" subtitle="Ingress vs Egress (MB/s)" icon={<NetworkIcon className="h-4 w-4" />}>
          <div className="h-64 w-full text-black dark:text-white">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trafficData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.1} vertical={false} />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'currentColor', opacity: 0.5 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'currentColor', opacity: 0.5 }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '0', border: '1px solid currentColor', background: 'var(--tw-bg-opacity, white)', color: 'currentColor' }}
                  itemStyle={{ color: 'currentColor' }}
                />
                <Legend iconType="square" wrapperStyle={{ fontSize: '10px', fontFamily: 'monospace', textTransform: 'uppercase' }} />
                <Line type="monotone" dataKey="ingress" stroke="currentColor" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'currentColor' }} name="Ingress" />
                <Line type="monotone" dataKey="egress" stroke="currentColor" strokeOpacity={0.4} strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'currentColor' }} name="Egress" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Connection Protocols" subtitle="Top protocols by request count" icon={<Globe className="h-4 w-4" />}>
          <div className="h-64 w-full text-black dark:text-white">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={connectionTypes} margin={{ top: 5, right: 20, bottom: 5, left: 0 }} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.1} horizontal={false} />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'currentColor', opacity: 0.5 }} />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'currentColor', opacity: 0.5 }} width={60} />
                <Tooltip 
                  contentStyle={{ borderRadius: '0', border: '1px solid currentColor', background: 'var(--tw-bg-opacity, white)', color: 'currentColor' }}
                  cursor={{ fill: 'currentColor', opacity: 0.05 }}
                  itemStyle={{ color: 'currentColor' }}
                />
                <Bar dataKey="count" fill="currentColor" radius={[0, 0, 0, 0]} name="Requests" barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="mt-6 overflow-hidden rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black">
        <div className="border-b border-black/10 px-6 py-4 dark:border-white/10">
          <h3 className="text-[15px] font-semibold tracking-tight text-black dark:text-white">Connection Nodes</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-black/10 text-[10px] font-mono uppercase tracking-wider text-black/60 dark:border-white/10 dark:text-white/60">
                <th className="px-6 py-3 font-medium">Source IP</th>
                <th className="px-6 py-3 font-medium">Destination</th>
                <th className="px-6 py-3 font-medium">Location</th>
                <th className="px-6 py-3 font-medium">Logins</th>
                <th className="px-6 py-3 font-medium">Failed</th>
                <th className="px-6 py-3 font-medium">Suspicious</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/10 dark:divide-white/10">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[10px] font-mono uppercase tracking-wider text-black/40 dark:text-white/40">
                    Loading network data...
                  </td>
                </tr>
              ) : nodes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[10px] font-mono uppercase tracking-wider text-black/40 dark:text-white/40">
                    No network data found.
                  </td>
                </tr>
              ) : (
                nodes.map((node, i) => (
                <tr key={i} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-black dark:text-white">{node.sourceIp}</td>
                  <td className="px-6 py-4 text-sm text-black/60 dark:text-white/60">{node.destination}</td>
                  <td className="px-6 py-4 text-sm text-black/60 dark:text-white/60">{node.geoLocation}</td>
                  <td className="px-6 py-4 text-sm text-black dark:text-white">{node.loginCount}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex h-6 items-center rounded-none border px-2.5 text-[10px] font-mono font-semibold uppercase tracking-wider ${node.failedLogins > 10 ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black' : 'border-black/20 bg-transparent text-black/40 dark:border-white/20 dark:text-white/40'}`}>
                      {node.failedLogins}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex h-6 items-center rounded-none border px-2.5 text-[10px] font-mono font-semibold uppercase tracking-wider ${node.suspiciousConnections > 0 ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black' : 'border-black/20 bg-transparent text-black/40 dark:border-white/20 dark:text-white/40'}`}>
                      {node.suspiciousConnections}
                    </span>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
