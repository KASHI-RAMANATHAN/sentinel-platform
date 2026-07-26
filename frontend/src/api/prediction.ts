import apiClient from './client';

export interface LogRecordRequest {
  timestamp?: string | null;
  login_hour?: number | null;
  day_of_week?: number | null;
  session_duration: number;
  command_length: number;
  unique_resources: number;
  failed_login_count: number;
  is_known_device: number;
  is_known_location: number;
  user_id?: string | null;
  username?: string | null;
  source_ip?: string | null;
  device_id?: string | null;
  resource?: string | null;
  login_method?: string | null;
  login_success?: boolean | null;
}

export interface ShapFeatureContribution {
  feature: string;
  shap_value: number;
  description: string;
}

export interface PredictionResponse {
  is_anomaly: boolean;
  risk_score: number;
  predicted_attack: string;
  confidence: number;
  explanation: ShapFeatureContribution[];
  explanation_summary: string;
  user_id?: string | null;
  source_ip?: string | null;
  device_id?: string | null;
  anomaly_score_raw: number;
  model_version: string;
  generated_at: string;
}

export const PredictionAPI = {
  /**
   * Evaluates a single log record through the ML pipeline to predict risk.
   */
  predictRisk: async (record: LogRecordRequest): Promise<PredictionResponse> => {
    return apiClient.post<PredictionResponse, PredictionResponse>('/predict', record);
  },
};
