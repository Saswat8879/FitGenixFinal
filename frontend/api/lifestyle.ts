import api from './axios';
import { StressResult, LifestyleCheckin, LifestyleCheckinOut, Tips, PostureStatus } from '@/lib/types';

export interface StressCheckRequest {
  heart_rate?: number;
  sleep_hours?: number;
  perceived_stress?: number;
  notes?: string;
}

export const lifestyleApi = {
  stressCheck: async (data?: StressCheckRequest): Promise<StressResult> => {
    const response = await api.post<StressResult>('/lifestyle/stress-check', data || {});
    return response.data;
  },

  checkin: async (data: LifestyleCheckin): Promise<LifestyleCheckinOut> => {
    const response = await api.post<LifestyleCheckinOut>('/lifestyle/checkin', data);
    return response.data;
  },

  getTips: async (): Promise<Tips> => {
    const response = await api.get<Tips>('/lifestyle/tips');
    return response.data;
  },

  getPosture: async (): Promise<PostureStatus> => {
    const response = await api.get<PostureStatus>('/lifestyle/posture');
    return response.data;
  },
};

export default lifestyleApi;
