import api from './axios';
import { FitStatus, FitConnectResponse } from '@/lib/types';

export const fitApi = {
  connect: async (): Promise<FitConnectResponse> => {
    const response = await api.get<FitConnectResponse>('/fit/connect');
    return response.data;
  },

  callback: async (code: string): Promise<{ message: string }> => {
    const response = await api.get<{ message: string }>('/fit/callback', {
      params: { code },
    });
    return response.data;
  },

  sync: async (days: number = 1): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/fit/sync', null, {
      params: { days },
    });
    return response.data;
  },

  getStatus: async (): Promise<FitStatus> => {
    const response = await api.get<FitStatus>('/fit/status');
    return response.data;
  },
};

export default fitApi;
