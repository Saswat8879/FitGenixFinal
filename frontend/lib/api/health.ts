import api from './axios';
import { HealthMetrics, RiskResult } from '@/lib/types';

export const healthApi = {
  getMetrics: async (): Promise<HealthMetrics> => {
    const response = await api.get<HealthMetrics>('/health/metrics');
    return response.data;
  },

  runDiabetesRisk: async (): Promise<RiskResult> => {
    const response = await api.post<RiskResult>('/health/risk/diabetes');
    return response.data;
  },

  runCvdRisk: async (): Promise<RiskResult> => {
    const response = await api.post<RiskResult>('/health/risk/cvd');
    return response.data;
  },

  refreshAllRisks: async (): Promise<{ diabetes: { score: number; category: string }; cvd: { score: number; category: string } }> => {
    const response = await api.post<{ diabetes: { score: number; category: string }; cvd: { score: number; category: string } }>('/health/risk/refresh');
    return response.data;
  },
};

export default healthApi;
