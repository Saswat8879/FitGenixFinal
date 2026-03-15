import api from './axios';
import { LifestylePoints } from '@/lib/types';

export const lifestylePointsApi = {
  getToday: async (): Promise<LifestylePoints> => {
    const response = await api.get<LifestylePoints>('/lifestyle-points/today');
    return response.data;
  },

  recompute: async (): Promise<LifestylePoints> => {
    const response = await api.post<LifestylePoints>('/lifestyle-points/recompute');
    return response.data;
  },

  getHistory: async (days: number = 30): Promise<LifestylePoints[]> => {
    const response = await api.get<LifestylePoints[]>('/lifestyle-points/history', {
      params: { days },
    });
    return response.data;
  },
};

export default lifestylePointsApi;
