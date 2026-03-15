import api from './axios';
import { Profile } from '@/lib/types';

export interface PersonalUpdate {
  name?: string;
  height_cm?: number;
  weight_kg?: number;
  age?: number;
}

export interface GoalsUpdate {
  goal?: string;
  coaching_style?: string;
  time_available_min?: number;
  activity_level?: string;
}

export interface DietUpdate {
  diet_type?: string;
  cuisine_preference?: string;
  equipment?: string[];
}

export interface ConditionsUpdate {
  type_2_diabetes?: boolean;
  pre_diabetes?: boolean;
  hypertension?: boolean;
  high_cholesterol?: boolean;
  fatty_liver?: boolean;
  obesity?: boolean;
  asthma_copd?: boolean;
  back_pain?: boolean;
  knee_pain?: boolean;
  shoulder_pain?: boolean;
  family_history_diabetes?: boolean;
  on_medication?: boolean;
  doctor_supervised?: boolean;
}

export interface NotificationsUpdate {
  preferred_notifications: boolean;
}

export interface ProfileUpdateResponse {
  message: string;
  plans_regenerated?: boolean;
}

export const profileApi = {
  getProfile: async (): Promise<Profile> => {
    const response = await api.get<Profile>('/profile/');
    return response.data;
  },

  updatePersonal: async (data: PersonalUpdate): Promise<ProfileUpdateResponse> => {
    const response = await api.patch<ProfileUpdateResponse>('/profile/personal', data);
    return response.data;
  },

  updateGoals: async (data: GoalsUpdate): Promise<ProfileUpdateResponse> => {
    const response = await api.patch<ProfileUpdateResponse>('/profile/goals', data);
    return response.data;
  },

  updateDiet: async (data: DietUpdate): Promise<ProfileUpdateResponse> => {
    const response = await api.patch<ProfileUpdateResponse>('/profile/diet', data);
    return response.data;
  },

  updateConditions: async (data: ConditionsUpdate): Promise<ProfileUpdateResponse> => {
    const response = await api.patch<ProfileUpdateResponse>('/profile/conditions', data);
    return response.data;
  },

  updateNotifications: async (data: NotificationsUpdate): Promise<ProfileUpdateResponse> => {
    const response = await api.patch<ProfileUpdateResponse>('/profile/notifications', data);
    return response.data;
  },
};

export default profileApi;
