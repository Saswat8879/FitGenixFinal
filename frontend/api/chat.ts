import api from './axios';
import { ChatMessage, ChatResponse } from '@/lib/types';

export const chatApi = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/', { message });
    return response.data;
  },

  getHistory: async (limit: number = 50): Promise<ChatMessage[]> => {
    const response = await api.get<ChatMessage[]>('/chat/history', {
      params: { limit },
    });
    return response.data;
  },

  clear: async (): Promise<void> => {
    await api.delete('/chat/history');
  },
};

export default chatApi;
