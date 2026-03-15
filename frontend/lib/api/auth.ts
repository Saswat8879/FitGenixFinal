import api from './axios';
import { ForgotPasswordResponse, ResetPasswordRequest, Token, User, UserLogin, UserRegister } from '@/lib/types';

export const authApi = {
  register: async (data: UserRegister): Promise<Token> => {
    const response = await api.post<Token>('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', { email, password });
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<Token> => {
    const response = await api.post<Token>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  forgotPassword: async (email: string): Promise<ForgotPasswordResponse> => {
    const response = await api.post<ForgotPasswordResponse>('/auth/forgot-password', { email });
    return response.data;
  },

  resetPassword: async (data: ResetPasswordRequest): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/reset-password', data);
    return response.data;
  },
};

export default authApi;
