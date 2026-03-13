import api from './axios';
import { OnboardingSurvey, OnboardingResponse } from '@/lib/types';

export const onboardingApi = {
  submitSurvey: async (data: OnboardingSurvey): Promise<OnboardingResponse> => {
    const response = await api.post<OnboardingResponse>('/onboarding/survey', data);
    return response.data;
  },
};

export default onboardingApi;
