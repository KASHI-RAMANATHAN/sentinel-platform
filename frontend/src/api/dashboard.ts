import apiClient from './client';

export interface DashboardStats {
  total_sessions: number;
  active_threats: number;
  average_risk_score: number;
  devices_monitored: number;
}

export interface AnomalyPoint {
  time: string;
  anomalies: number;
  normal: number;
}

export interface AttackType {
  label: string;
  value: number;
  color: string;
}

interface TrendBackendResponse {
  labels: string[];
  normal: number[];
  anomaly: number[];
}

interface DistributionBackendResponse {
  labels: string[];
  values: number[];
}

interface NetworkTrafficBackendResponse {
  labels: string[];
  ingress: number[];
  egress: number[];
}

interface ConnectionProtocol {
  name: string;
  count: number;
}

interface ConnectionProtocolsBackendResponse {
  protocols: ConnectionProtocol[];
}

const COLORS = [
  "fill-black dark:fill-white", 
  "fill-black/80 dark:fill-white/80", 
  "fill-black/60 dark:fill-white/60", 
  "fill-black/40 dark:fill-white/40", 
  "fill-black/20 dark:fill-white/20"
];

export const DashboardAPI = {
  /**
   * Fetches the top-level KPI statistics for the dashboard.
   */
  getStats: async (): Promise<DashboardStats> => {
    return apiClient.get<DashboardStats, DashboardStats>('/dashboard/stats');
  },

  /**
   * Fetches the anomaly trend data for the line chart.
   */
  getTrends: async (): Promise<AnomalyPoint[]> => {
    const res = await apiClient.get<TrendBackendResponse, TrendBackendResponse>('/dashboard/trends');
    if (!res?.labels || !res?.normal || !res?.anomaly) return [];
    
    return res.labels.map((label, idx) => ({
      time: label,
      anomalies: res.anomaly[idx] || 0,
      normal: res.normal[idx] || 0
    }));
  },

  /**
   * Fetches the attack distribution data for the pie chart.
   */
  getDistribution: async (): Promise<AttackType[]> => {
    const res = await apiClient.get<DistributionBackendResponse, DistributionBackendResponse>('/dashboard/distribution');
    if (!res?.labels || !res?.values) return [];
    
    return res.labels.map((label, idx) => ({
      label: label,
      value: res.values[idx] || 0,
      color: COLORS[idx % COLORS.length]
    }));
  },

  /**
   * Fetches the network traffic data (ingress vs egress).
   */
  getNetworkTraffic: async () => {
    const res = await apiClient.get<NetworkTrafficBackendResponse, NetworkTrafficBackendResponse>('/dashboard/network');
    if (!res?.labels || !res?.ingress || !res?.egress) return [];
    
    return res.labels.map((label, idx) => ({
      time: label,
      ingress: res.ingress[idx] || 0,
      egress: res.egress[idx] || 0
    }));
  },

  /**
   * Fetches the connection protocols (auth methods).
   */
  getConnectionProtocols: async () => {
    const res = await apiClient.get<ConnectionProtocolsBackendResponse, ConnectionProtocolsBackendResponse>('/dashboard/protocols');
    if (!res?.protocols) return [];
    
    return res.protocols;
  },
};
