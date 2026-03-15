import api from './axios';
import { WeightLog, WeightLogResponse, GoalProgress, TrendPoint, PlatformAverage } from '@/lib/types';

export interface WeightLogRequest {
  weight_kg: number;
  notes?: string;
}

export const progressApi = {
  logWeight: async (data: WeightLogRequest): Promise<WeightLogResponse> => {
    const response = await api.post<WeightLogResponse>('/progress/weight', data);
    return response.data;
  },

  getWeightHistory: async (days: number = 90): Promise<WeightLog[]> => {
    const response = await api.get<WeightLog[]>('/progress/weight', {
      params: { days },
    });
    return response.data;
  },

  getGoalProgress: async (): Promise<GoalProgress> => {
    const response = await api.get<GoalProgress>('/progress/goal');
    return response.data;
  },

  getLifestylePointsTrend: async (days: number = 30): Promise<TrendPoint[]> => {
    const response = await api.get<TrendPoint[]>('/progress/lifestyle-points', {
      params: { days },
    });
    return response.data;
  },

  getPlatformAverage: async (): Promise<PlatformAverage> => {
    const response = await api.get<PlatformAverage>('/progress/platform-average');
    return response.data;
  },
};

export default progressApi;
