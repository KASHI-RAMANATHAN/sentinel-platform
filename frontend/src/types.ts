export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'resolved';
export type AlertStatus = 'investigating' | 'open' | 'resolved' | 'blocked';

export interface Alert {
  id: string;
  title: string;
  severity: Severity;
  status: AlertStatus;
  source: string;
  destination: string;
  category: string;
  timestamp: string;
  riskScore: number;
  description: string;
  protocol: string;
  port: number;
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

export interface Kpi {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down';
  positive: boolean;
  icon: 'sessions' | 'threats' | 'risk' | 'devices';
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  badge?: string;
}
