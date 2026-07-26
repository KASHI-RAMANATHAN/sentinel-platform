import { useState } from 'react';
import Badge from '@/components/dashboard/Badge';

interface DetectionRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

const initialRules: DetectionRule[] = [
  { id: 'rule-01', name: 'Brute Force Detection', description: 'Detects multiple failed login attempts from a single IP within 5 minutes.', enabled: true, severity: 'high' },
  { id: 'rule-02', name: 'Impossible Travel', description: 'Flags logins from geographically distant locations occurring within an impossible timeframe.', enabled: true, severity: 'critical' },
  { id: 'rule-03', name: 'Credential Stuffing', description: 'Monitors for mass login attempts using leaked credential databases.', enabled: true, severity: 'critical' },
  { id: 'rule-04', name: 'New Device Login', description: 'Alerts when a user logs in from a device fingerprint never seen before.', enabled: false, severity: 'medium' },
  { id: 'rule-05', name: 'Lateral Movement', description: 'Identifies suspicious internal network traversal by non-admin accounts.', enabled: true, severity: 'high' },
  { id: 'rule-06', name: 'DLP Trigger', description: 'Data exfiltration attempts via unauthorized cloud storage providers.', enabled: true, severity: 'high' },
  { id: 'rule-07', name: 'Off-Hours Access', description: 'Monitors successful logins outside of standard operating hours (8 PM - 6 AM).', enabled: false, severity: 'low' },
];

export default function DetectionRules() {
  const [rules, setRules] = useState<DetectionRule[]>(initialRules);

  const toggleRule = (id: string) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Detection Rules</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Manage active security policies and threat detection heuristics
          </p>
        </div>
      </div>

      <div className="mt-6 overflow-hidden rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-black/10 text-[10px] font-mono uppercase tracking-wider text-black/60 dark:border-white/10 dark:text-white/60">
                <th className="px-6 py-3 font-medium">Rule Name</th>
                <th className="px-6 py-3 font-medium">Description</th>
                <th className="px-6 py-3 font-medium">Severity</th>
                <th className="px-6 py-3 font-medium text-right">Enabled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/10 dark:divide-white/10">
              {rules.map(rule => (
                <tr key={rule.id} className="hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 font-medium text-sm text-black whitespace-nowrap dark:text-white">{rule.name}</td>
                  <td className="px-6 py-4 text-sm text-black/60 max-w-md truncate dark:text-white/60" title={rule.description}>{rule.description}</td>
                  <td className="px-6 py-4">
                    <Badge variant="severity" value={rule.severity} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => toggleRule(rule.id)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-none border transition-colors ${
                        rule.enabled ? 'border-black bg-black dark:border-white dark:bg-white' : 'border-black/20 bg-transparent dark:border-white/20'
                      }`}
                    >
                      <span className="sr-only">Toggle rule</span>
                      <span
                        className={`inline-block h-4 w-4 transform rounded-none transition-transform ${
                          rule.enabled ? 'translate-x-6 bg-white dark:bg-black' : 'translate-x-1 bg-black/40 dark:bg-white/40'
                        } shadow-sm`}
                      />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
