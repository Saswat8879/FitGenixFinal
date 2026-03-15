import api from './axios';
import { DashboardData, DashboardTrends } from '@/lib/types';

export const dashboardApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get<DashboardData>('/dashboard/');
    return response.data;
  },

  getTrends: async (days: number = 14): Promise<DashboardTrends> => {
    const response = await api.get<DashboardTrends>('/dashboard/trends', {
      params: { days },
    });
    return response.data;
  },
};

export default dashboardApi;
