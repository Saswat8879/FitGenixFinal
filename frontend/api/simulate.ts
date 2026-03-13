import api from './axios';
import { SimulationResponse } from '@/lib/types';

export const simulateApi = {
  fullDay: async (): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate/full-day');
    return response.data;
  },

  stressSpike: async (): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate/stress-spike');
    return response.data;
  },

  weightTrend: async (direction: 'loss' | 'gain' | 'plateau', days: number = 30): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate/weight-trend', {
      direction,
      days,
    });
    return response.data;
  },

  mealLog: async (): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate/meal-log');
    return response.data;
  },

  workoutComplete: async (): Promise<SimulationResponse> => {
    const response = await api.post<SimulationResponse>('/simulate/workout-complete');
    return response.data;
  },

  reset: async (): Promise<{ message: string; deleted: Record<string, number> }> => {
    const response = await api.post<{ message: string; deleted: Record<string, number> }>('/simulate/reset');
    return response.data;
  },
};

export default simulateApi;
