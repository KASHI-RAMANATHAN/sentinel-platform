import apiClient from './client';

export interface StepSummary {
  name: string;
  success: boolean;
  rows_in: number;
  rows_out: number;
  duration_s: number;
  detail: string;
  error?: string | null;
}

export interface UploadResponse {
  success: boolean;
  processed_records: number;
  anomalies_detected: number;
  alerts_created: number;
  message: string;
}

export const UploadAPI = {
  /**
   * Uploads a CSV file of raw access logs to the ML pipeline.
   */
  uploadCsv: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post<UploadResponse, UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};
