import { useState, useEffect } from 'react';
import DevicesTable, { type Device } from '@/components/dashboard/DevicesTable';
import { AlertsAPI } from '@/api/alerts';
import type { Alert } from '@/types';

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Generate devices dynamically from the alerts dataset
    const fetchDevices = async () => {
      try {
        setLoading(true);
        const alertsData = await AlertsAPI.getAlerts();
        const rawAlerts = alertsData?.alerts ?? [];
        
        const deviceMap = new Map<string, Device>();

        rawAlerts.forEach(a => {
          const deviceId = a.device_id && a.device_id !== 'Unknown Script/Bot' ? a.device_id : `Unknown-${a.ip || 'Device'}`;
          
          if (!deviceMap.has(deviceId)) {
            deviceMap.set(deviceId, {
              id: deviceId,
              type: deviceId.includes('macOS') || deviceId.includes('Windows') ? 'Workstation' : (deviceId.includes('Server') ? 'Server' : 'Unknown'),
              user: a.user_id || 'Unknown',
              riskScore: a.risk ?? 0,
              status: 'active',
              lastSeen: a.timestamp ? new Date(a.timestamp).toLocaleString() : 'Unknown',
            });
          } else {
            const existing = deviceMap.get(deviceId)!;
            existing.riskScore = Math.max(existing.riskScore, a.risk ?? 0);
            if ((a.risk ?? 0) > 80) existing.status = 'compromised';
            deviceMap.set(deviceId, existing);
          }
        });

        const deviceList = Array.from(deviceMap.values()).sort((a, b) => b.riskScore - a.riskScore);
        
        // Add some mock devices if none exist, just to show the UI
        if (deviceList.length === 0) {
          deviceList.push(
            { id: 'FIN-WS-014', type: 'Workstation', user: 'j.mercer', riskScore: 81, status: 'compromised', lastSeen: '10 min ago' },
            { id: 'HR-WS-042', type: 'Workstation', user: 'a.smith', riskScore: 25, status: 'active', lastSeen: '2 hours ago' },
            { id: 'DC-INTERNAL-02', type: 'Server', user: 'SYSTEM', riskScore: 12, status: 'active', lastSeen: '1 min ago' },
            { id: 'OLD-LAPTOP-09', type: 'Workstation', user: 'Unknown', riskScore: 50, status: 'inactive', lastSeen: '3 days ago' },
          );
        }

        setDevices(deviceList);
      } catch (err) {
        setError('Failed to load devices.');
      } finally {
        setLoading(false);
      }
    };

    fetchDevices();
  }, []);

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-black dark:text-white">Devices</h1>
          <p className="mt-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-black/60 dark:text-white/60">
            Monitor all endpoints and infrastructure assets
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-2xl bg-red-500/10 p-4 text-sm text-red-500 border border-red-500/20">
          {error}
        </div>
      )}

      {loading ? (
        <div className="mt-6 flex h-64 items-center justify-center rounded-none border border-black/20 bg-white dark:border-white/20 dark:bg-black">
          <div className="text-[10px] font-mono uppercase tracking-wider text-black/40 dark:text-white/40">Loading devices...</div>
        </div>
      ) : (
        <DevicesTable devices={devices} />
      )}
    </>
  );
}
