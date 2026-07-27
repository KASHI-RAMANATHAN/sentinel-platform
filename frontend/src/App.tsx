import { useEffect, useState, useCallback, useRef } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import TopNav from '@/components/layout/TopNav';
import AmbientBackground from '@/components/layout/AmbientBackground';
import { ShieldAlert } from 'lucide-react';
import VoidLogo from '@/components/VoidLogo';

import type { Alert, Kpi } from '@/types';
import { DashboardAPI, type AnomalyPoint, type AttackType, type DashboardStats } from '@/api/dashboard';
import { AlertsAPI } from '@/api/alerts';

// Pages
import Overview from '@/pages/Overview';
import Alerts from '@/pages/Alerts';
import Devices from '@/pages/Devices';
import Network from '@/pages/Network';
import Reports from '@/pages/Reports';
import DetectionRules from '@/pages/DetectionRules';
import AuditLog from './pages/AuditLog';
import About from '@/pages/About';
import { db } from './lib/firebase';
import { doc, setDoc, collection, addDoc } from 'firebase/firestore';

const BASE_KPIS: Kpi[] = [
  { label: 'Total Sessions', value: '0', delta: '+0%', trend: 'up', positive: true, icon: 'sessions' },
  { label: 'Active Threats', value: '0', delta: '+0%', trend: 'up', positive: false, icon: 'threats' },
  { label: 'Average Risk Score', value: '0', delta: '-0%', trend: 'down', positive: true, icon: 'risk' },
  { label: 'Devices Monitored', value: '0', delta: '+0%', trend: 'up', positive: true, icon: 'devices' },
];

function getEventName(attackType: string): string {
  const map: Record<string, string> = {
    'Credential Abuse': 'Credential Abuse',
    'Impossible Travel': 'Impossible Travel',
    'Session Hijacking': 'Session Hijacking',
    'Insider Threat': 'Insider Threat',
    'Behavioral Anomaly': 'Behavioral Anomaly',
    'Brute Force': 'Multiple Failed Logins',
    'Credential Stuffing': 'Credential Abuse',
    'Device Spoofing': 'Suspicious Login',
    'Lateral Movement': 'Privilege Escalation',
    'Low and Slow Exfiltration': 'Unauthorized Resource Access',
    'Insider Drift': 'Insider Threat',
  };
  return map[attackType] || 'Suspicious Login';
}

export default function App() {
  const [activeNav, setActiveNav] = useState('overview');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const isInitialLoadRef = useRef(true);
  const [isRetrying, setIsRetrying] = useState(false);
  
  const [liveStats, setLiveStats] = useState<DashboardStats | null>(null);
  const [liveKpis, setLiveKpis] = useState<Kpi[]>(BASE_KPIS);
  const [statsError, setStatsError] = useState<string | null>(null);

  const [liveAlerts, setLiveAlerts] = useState<Alert[]>([]);
  const [alertsError, setAlertsError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [toastMessage, setToastMessage] = useState<{title: string, text: string} | null>(null);

  const [liveTrend, setLiveTrend] = useState<AnomalyPoint[]>([]);
  const [liveDistribution, setLiveDistribution] = useState<AttackType[]>([]);
  const [chartsError, setChartsError] = useState<string | null>(null);

  // Dark Mode State
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('sentinel_theme');
    return saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches);
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
      localStorage.setItem('sentinel_theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('sentinel_theme', 'light');
    }
  }, [isDarkMode]);

  const toggleDarkMode = useCallback(() => {
    setIsDarkMode(prev => !prev);
  }, []);

  const fetchDashboardData = useCallback(async () => {
    const isInitial = isInitialLoadRef.current;
    if (isInitial) {
      setLoading(true);
    }
    
    let attempt = 0;
    const maxAttempts = 5;
    const delays = [3000, 6000, 12000, 24000];

    while (attempt < maxAttempts) {
      setStatsError(null);
      setChartsError(null);
      setAlertsError(null);

      let statsSuccess = false;
      let chartsSuccess = false;
      let alertsSuccess = false;

      let tempStatsError = null;
      let tempChartsError = null;
      let tempAlertsError = null;

      try {
        const stats = await DashboardAPI.getStats();
        setLiveStats(stats);
        
        const prevStatsStr = localStorage.getItem('sentinel_prev_stats');
        const prevStats: DashboardStats | null = prevStatsStr ? JSON.parse(prevStatsStr) : null;
        
        const calc = (cur: number, prev: number, inverse: boolean = false) => {
          if (prev === 0 && cur === 0) return { delta: '--', trend: 'up' as const, positive: true };
          if (prev === 0) return { delta: '--', trend: 'up' as const, positive: !inverse };
          const diff = cur - prev;
          const pct = Math.round((diff / prev) * 100);
          const trend = diff >= 0 ? 'up' : 'down';
          const sign = diff > 0 ? '+' : '';
          const isPositive = inverse ? diff <= 0 : diff >= 0;
          return { delta: `${sign}${pct}%`, trend: trend as 'up'|'down', positive: isPositive };
        };

        if (!prevStats) {
          setLiveKpis([
            { ...BASE_KPIS[0], value: (stats?.total_sessions ?? 0).toLocaleString(), delta: '--' },
            { ...BASE_KPIS[1], value: (stats?.active_threats ?? 0).toLocaleString(), delta: '--' },
            { ...BASE_KPIS[2], value: (stats?.average_risk_score ?? 0).toFixed(1), delta: '--' },
            { ...BASE_KPIS[3], value: (stats?.devices_monitored ?? 0).toLocaleString(), delta: '--' },
          ]);
        } else {
          setLiveKpis([
            { ...BASE_KPIS[0], value: (stats?.total_sessions ?? 0).toLocaleString(), ...calc(stats?.total_sessions ?? 0, prevStats.total_sessions) },
            { ...BASE_KPIS[1], value: (stats?.active_threats ?? 0).toLocaleString(), ...calc(stats?.active_threats ?? 0, prevStats.active_threats, true) },
            { ...BASE_KPIS[2], value: (stats?.average_risk_score ?? 0).toFixed(1), ...calc(stats?.average_risk_score ?? 0, prevStats.average_risk_score, true) },
            { ...BASE_KPIS[3], value: (stats?.devices_monitored ?? 0).toLocaleString(), ...calc(stats?.devices_monitored ?? 0, prevStats.devices_monitored) },
          ]);
        }

        if (!stats || stats.total_sessions === 0) {
          throw new Error('Data not ready (total_sessions is 0)');
        }

        localStorage.setItem('sentinel_prev_stats', JSON.stringify(stats));
        statsSuccess = true;
      } catch (err) {
        tempStatsError = 'Failed to load dashboard statistics.';
      }

      try {
        const [trendData, distData] = await Promise.all([
          DashboardAPI.getTrends(),
          DashboardAPI.getDistribution(),
        ]);
        setLiveTrend(trendData);
        setLiveDistribution(distData);
        chartsSuccess = true;
      } catch (err) {
        tempChartsError = 'Failed to load chart data.';
      }

      try {
        const alertsData = await AlertsAPI.getAlerts();
        const rawAlerts = alertsData?.alerts ?? [];
        const mappedAlerts: Alert[] = rawAlerts.map(a => ({
          id: a.id,
          title: getEventName(a.attack_type),
          severity: (a.severity === 'critical' || a.severity === 'high' || a.severity === 'medium' || a.severity === 'low') ? a.severity : 'medium',
          status: (a.status === 'in_progress' ? 'investigating' : (a.status === 'false_positive' ? 'resolved' : a.status)) as any,
          source: a.ip || 'Unknown',
          destination: a.device_id || 'Unknown',
          category: a.attack_type,
          timestamp: a.timestamp ? new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown',
          riskScore: Math.round(a.risk ?? 0),
          description: `User: ${a.user_id || 'Unknown'} - Anomaly Score: ${(a.anomaly_score ?? 0).toFixed(2)}`,
          protocol: 'TCP',
          port: 443,
        })).sort((a, b) => b.riskScore - a.riskScore);

        setLiveAlerts(mappedAlerts);
        if (mappedAlerts.length > 0) {
          setSelectedAlert(mappedAlerts[0]);
        } else {
          setSelectedAlert(null);
        }
        alertsSuccess = true;
      } catch (err) {
        tempAlertsError = 'Failed to load live alerts.';
        setLiveAlerts([]);
        setSelectedAlert(null);
      }

      const allSuccess = statsSuccess && chartsSuccess && alertsSuccess;

      if (!isInitial || allSuccess) {
        if (!statsSuccess) setStatsError(tempStatsError);
        if (!chartsSuccess) setChartsError(tempChartsError);
        if (!alertsSuccess) setAlertsError(tempAlertsError);
        break;
      }

      attempt++;
      if (attempt >= maxAttempts) {
        if (!statsSuccess) setStatsError(tempStatsError);
        if (!chartsSuccess) setChartsError(tempChartsError);
        if (!alertsSuccess) setAlertsError(tempAlertsError);
        break;
      }

      setIsRetrying(true);
      await new Promise(resolve => setTimeout(resolve, delays[attempt - 1] || 12000));
    }

    if (isInitial) {
      isInitialLoadRef.current = false;
      setIsInitialLoad(false);
      setIsRetrying(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const intervalId = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(intervalId);
  }, [fetchDashboardData]);

  const handleInvestigate = useCallback(async (alertId: string) => {
    // Optimistic UI update
    setLiveAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'investigating' } : a));
    setSelectedAlert(prev => prev?.id === alertId ? { ...prev, status: 'investigating' } : prev);
    setToastMessage({ title: 'Investigating', text: 'Alert assigned for investigation.' });
    setTimeout(() => setToastMessage(null), 3000);

    try {
        const alertRef = doc(db, 'alerts', alertId);
        await setDoc(alertRef, {
            status: 'investigating',
            investigated_by: 'SOC Analyst',
            investigated_at: new Date().toISOString()
        }, { merge: true });

        await addDoc(collection(db, 'audit_logs'), {
            log_id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7),
            timestamp: new Date().toISOString(),
            actor: 'SOC Analyst',
            action: 'Investigated Alert',
            category: 'Analyst',
            resource: 'alert',
            status: 'Success',
            details: `Analyst assigned to investigate alert ${alertId}.`,
            alert_id: alertId
        });
    } catch (e) {
        console.error('Error investigating alert in Firestore:', e);
    }
  }, []);

  const handleResolve = useCallback(async (alertId: string) => {
    // Optimistic UI update
    setLiveAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'resolved', severity: 'resolved', riskScore: 0 } : a));
    setSelectedAlert(prev => prev?.id === alertId ? { ...prev, status: 'resolved', severity: 'resolved', riskScore: 0 } : prev);
    
    setLiveStats(prev => prev ? { ...prev, active_threats: Math.max(0, prev.active_threats - 1) } : null);
    setLiveKpis(prev => {
        const threatsKpi = prev[1];
        let oldVal = parseInt(threatsKpi.value.replace(/,/g, ''));
        if (isNaN(oldVal)) oldVal = 0;
        const newCount = Math.max(0, oldVal - 1);
        return [
            prev[0],
            { ...threatsKpi, value: newCount.toLocaleString() },
            prev[2],
            prev[3]
        ];
    });
    setToastMessage({ title: 'Resolved', text: 'Alert resolved and risk score set to 0.' });
    setTimeout(() => setToastMessage(null), 3000);

    try {
        const alertRef = doc(db, 'alerts', alertId);
        await setDoc(alertRef, {
            status: 'resolved',
            risk_score: 0,
            severity: 'resolved',
            resolved_by: 'SOC Analyst',
            resolved_at: new Date().toISOString()
        }, { merge: true });

        await addDoc(collection(db, 'audit_logs'), {
            log_id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7),
            timestamp: new Date().toISOString(),
            actor: 'SOC Analyst',
            action: 'Resolved Alert',
            category: 'Analyst',
            resource: 'alert',
            status: 'Success',
            details: `Analyst resolved alert ${alertId}.`,
            alert_id: alertId
        });
    } catch (e) {
        console.error('Error resolving alert in Firestore:', e);
    }
  }, []);

  const renderContent = () => {
    switch (activeNav) {
      case 'overview':
        return (
          <Overview 
            loading={loading}
            liveStats={liveStats}
            liveKpis={liveKpis}
            statsError={statsError}
            liveTrend={liveTrend}
            liveDistribution={liveDistribution}
            chartsError={chartsError}
            liveAlerts={liveAlerts}
            alertsError={alertsError}
            selectedAlert={selectedAlert}
            setSelectedAlert={setSelectedAlert}
            fetchDashboardData={fetchDashboardData}
            onInvestigate={handleInvestigate}
            onResolve={handleResolve}
          />
        );
      case 'alerts':
        return (
          <Alerts 
            alerts={liveAlerts} 
            loading={loading} 
            error={alertsError} 
            onInvestigate={handleInvestigate}
            onResolve={handleResolve}
          />
        );
      case 'devices':
        return <Devices />;
      case 'network':
        return <Network />;
      case 'reports':
        return (
          <Reports 
            loading={loading}
            liveStats={liveStats}
            liveKpis={liveKpis}
            statsError={statsError}
            liveTrend={liveTrend}
            liveDistribution={liveDistribution}
            chartsError={chartsError}
            liveAlerts={liveAlerts}
          />
        );
      case 'rules':
        return <DetectionRules />;
      case 'audit':
        return <AuditLog />;
      case 'about':
        return <About />;
      default:
        return <Overview {...{
            loading, liveStats, liveKpis, statsError, liveTrend, liveDistribution,
            chartsError, liveAlerts, alertsError, selectedAlert, setSelectedAlert, fetchDashboardData,
            onInvestigate: handleInvestigate, onResolve: handleResolve
        }} />;
    }
  };

  if (isInitialLoad && loading) {
    return (
      <div className="relative min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center font-mono selection:bg-emerald-500/30">
        <AmbientBackground />
        <div className="relative z-10 flex flex-col items-center justify-center">
          <div className="mb-8 flex items-center justify-center">
            <VoidLogo className="h-20 w-20 text-white animate-pulse" />
          </div>
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tighter text-white mb-4">
              Sentinel
            </h1>
            <p className="text-xs md:text-sm uppercase tracking-[0.3em] text-emerald-500 font-semibold">
              Security Console
            </p>
          </div>
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-3 text-sm text-emerald-400">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              LOADING DASHBOARD...
            </div>
            {isRetrying && (
              <div className="mt-6 text-xs text-blue-400 max-w-sm text-center px-4 animate-pulse leading-relaxed">
                <span className="text-blue-500/70">&gt;</span> Waking up backend systems...
                <br />
                <span className="text-blue-500/70">&gt;</span> This may take up to a minute on first load.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />
      
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 rounded-2xl bg-slate-900 px-6 py-4 text-white shadow-xl animate-slide-in">
          <p className="text-sm font-semibold">{toastMessage.title}</p>
          <p className="mt-1 text-xs text-slate-300">{toastMessage.text}</p>
        </div>
      )}

      <div className="relative z-10">
        <Sidebar
          activeId={activeNav}
          onSelect={setActiveNav}
          mobileOpen={mobileSidebarOpen}
          onClose={() => setMobileSidebarOpen(false)}
          alertsCount={liveStats?.active_threats ?? 0}
        />

        <div className="lg:pl-72">
          <TopNav 
            onMenuClick={() => setMobileSidebarOpen(true)} 
            isDarkMode={isDarkMode}
            onToggleDarkMode={toggleDarkMode}
          />

          <main className="px-4 py-6 lg:px-8 lg:py-8">
            {renderContent()}

            <footer className="mt-8 flex flex-col gap-2 border-t border-black/5 pt-4 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">
              <span className="flex items-center gap-2">
                <ShieldAlert className="h-3.5 w-3.5 text-slate-400" />
                Sentinel Security Console
              </span>
              <span className="font-mono">v4.2.1 · build 2024.11.07</span>
            </footer>
          </main>
        </div>
      </div>
    </div>
  );
}
