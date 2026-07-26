import apiClient from './client';

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'resolved';
export type AlertStatus = 'open' | 'in_progress' | 'resolved' | 'false_positive';

// Legacy UI Types
export interface AlertItem {
  id: string;
  risk: number;
  severity: AlertSeverity;
  attack_type: string;
  status: AlertStatus;
  timestamp: string;
  user_id: string | null;
  device_id: string | null;
  ip: string | null;
  anomaly_score: number;
}

export interface PaginatedAlertResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  alerts: AlertItem[];
}

export interface ShapFeature {
  feature: string;
  shap_value: number;
  description: string;
}

export interface DeviceInfo {
  device_id: string;
  device_type: string | null;
  os: string | null;
  browser: string | null;
}

export interface GeoLocation {
  city: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface AlertDetail {
  id: string;
  risk: number;
  severity: AlertSeverity;
  attack_type: string;
  status: AlertStatus;
  timestamp: string;
  user_id: string | null;
  username: string | null;
  department: string | null;
  role: string | null;
  source_ip: string | null;
  login_method: string | null;
  resource_accessed: string | null;
  session_duration: number | null;
  login_success: boolean | null;
  device: DeviceInfo | null;
  geo_location: GeoLocation | null;
  shap_explanation: {
    top_features: ShapFeature[];
    summary: string;
  };
  recommended_action: string;
  anomaly_score: number;
}

// New Backend Types (AI Intelligence Layer)
interface BackendAlertItem {
  id: string;
  risk_score: number;
  severity: AlertSeverity;
  attack_type: string;
  status: AlertStatus;
  timestamp: string;
  entity_id: string | null;
  device_fingerprint: string | null;
  source_ip: string | null;
  anomaly_score: number;
}

interface BackendPaginatedResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  alerts: BackendAlertItem[];
}

interface BackendAlertDetail {
  id: string;
  timestamp: string;
  entity_id: string | null;
  entity_type: string | null;
  source_ip: string | null;
  geo_location: string | null;
  device_fingerprint: string | null;
  resource_accessed: string | null;
  auth_method: string | null;
  session_duration: number | null;
  command_sequence: string | null;
  login_success: boolean | null;
  label: string | null;
  risk_score: number;
  anomaly_score: number;
  prediction: number;
  attack_type: string;
  shap_explanation: {
    top_features: ShapFeature[];
    summary: string;
  };
}

export interface GetAlertsParams {
  page?: number;
  page_size?: number;
  severity?: AlertSeverity;
  status?: AlertStatus;
}

export const AlertsAPI = {
  getAlerts: async (params?: GetAlertsParams): Promise<PaginatedAlertResponse> => {
    const res = await apiClient.get<BackendPaginatedResponse, BackendPaginatedResponse>('/alerts', { params });
    
    // Map backend items to legacy UI items
    const mappedAlerts: AlertItem[] = res.alerts.map(a => ({
      id: a.id,
      risk: a.risk_score,
      severity: a.severity,
      attack_type: a.attack_type,
      status: a.status,
      timestamp: a.timestamp,
      user_id: a.entity_id,
      device_id: a.device_fingerprint,
      ip: a.source_ip,
      anomaly_score: a.anomaly_score
    }));

    return {
      total: res.total,
      page: res.page,
      page_size: res.page_size,
      total_pages: res.total_pages,
      alerts: mappedAlerts
    };
  },

  getAlertById: async (alertId: string): Promise<AlertDetail> => {
    const res = await apiClient.get<BackendAlertDetail, BackendAlertDetail>(`/alerts/${alertId}`);
    
    let city = null;
    let country = null;
    if (res.geo_location) {
        if (res.geo_location.includes(',')) {
            city = res.geo_location.split(',')[0].trim();
            country = res.geo_location.split(',')[1].trim();
        } else {
            country = res.geo_location;
        }
    }

    let device_id = 'Unknown Device';
    let os = null;
    let browser = null;
    if (res.device_fingerprint) {
        if (res.device_fingerprint.includes(' (')) {
            device_id = res.device_fingerprint.split(' (')[0];
            const details = res.device_fingerprint.split(' (')[1].replace(')', '');
            if (details.includes(' - ')) {
                os = details.split(' - ')[0];
                browser = details.split(' - ')[1];
            } else {
                os = details;
            }
        } else {
            device_id = res.device_fingerprint;
        }
    }

    // Since the new backend returns severity as string, but UI mapped it, we just pass severity along
    // But the backend doesn't provide severity/status directly in AlertDetail anymore?
    // Wait, AlertDetail doesn't have severity/status in my new BackendAlertDetail! 
    // Let me compute them or pass them
    let riskSeverity: AlertSeverity = 'low';
    if (res.risk_score > 80) riskSeverity = 'critical';
    else if (res.risk_score > 60) riskSeverity = 'high';
    else if (res.risk_score > 30) riskSeverity = 'medium';

    let recAction = 'Monitor activity.';
    if (res.prediction === -1) {
        switch (res.attack_type) {
            case 'Credential Abuse':
                recAction = 'Force password reset and mandate MFA re-authentication.';
                break;
            case 'Impossible Travel':
                recAction = 'Suspend user account pending identity verification.';
                break;
            case 'Session Hijacking':
                recAction = 'Terminate all active sessions and rotate access tokens immediately.';
                break;
            case 'Insider Threat':
                recAction = 'Alert line manager and temporarily restrict sensitive resource access.';
                break;
            default:
                recAction = 'Isolate entity and review recent access logs.';
                break;
        }
    }

    return {
      id: res.id,
      risk: res.risk_score,
      severity: riskSeverity,
      attack_type: res.attack_type,
      status: 'open',
      timestamp: res.timestamp,
      user_id: res.entity_id,
      username: res.entity_id,
      department: null,
      role: null,
      source_ip: res.source_ip,
      login_method: res.auth_method,
      resource_accessed: res.resource_accessed,
      session_duration: res.session_duration,
      login_success: res.login_success,
      device: res.device_fingerprint ? {
          device_id,
          device_type: null,
          os,
          browser
      } : null,
      geo_location: res.geo_location ? {
          city,
          country,
          latitude: null,
          longitude: null
      } : null,
      shap_explanation: res.shap_explanation,
      recommended_action: recAction,
      anomaly_score: res.anomaly_score
    };
  },
};
