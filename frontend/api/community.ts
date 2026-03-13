import api from './axios';
import { LeaderboardData, MyRank } from '@/lib/types';

export const communityApi = {
  getLeaderboard: async (topN: number = 20): Promise<LeaderboardData> => {
    const response = await api.get<LeaderboardData>('/community/leaderboard', {
      params: { top_n: topN },
    });
    return response.data;
  },

  getMyRank: async (): Promise<MyRank> => {
    const response = await api.get<MyRank>('/community/my-rank');
    return response.data;
  },
};

export default communityApi;
