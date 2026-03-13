import api from './axios';
import { MealSearchResult, MealLog, WaterLog, WaterToday } from '@/lib/types';

export interface MealFromPlanRequest {
  diet_plan_id: number;
  food_id?: number;
  food_name?: string;
  meal_slot: string;
  portion_g?: number;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
  sugar_g?: number;
  saturated_fat_g?: number;
}

export interface MealSearchRequest {
  query: string;
  meal_slot?: string;
}

export interface MealConfirmRequest {
  name: string;
  meal_slot: string;
  portion_g: number;
  calories: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
  sugar_g?: number;
  saturated_fat_g?: number;
}

export interface MealCustomRequest {
  food_name: string;
  meal_slot: string;
  portion_g?: number;
  calories: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
  sodium?: number;
  sugar?: number;
  saturated_fat?: number;
}

export interface WaterLogRequest {
  amount_ml: number;
  source?: string;
}

export const logsApi = {
  mealFromPlan: async (data: MealFromPlanRequest): Promise<MealLog> => {
    const response = await api.post<MealLog>('/logs/meal/from-plan', data);
    return response.data;
  },

  searchMeal: async (data: MealSearchRequest): Promise<MealSearchResult[]> => {
    const response = await api.post<MealSearchResult[]>('/logs/meal/search', data);
    return response.data;
  },

  confirmMeal: async (data: MealConfirmRequest): Promise<MealLog> => {
    const response = await api.post<MealLog>('/logs/meal/confirm', data);
    return response.data;
  },

  customMeal: async (data: MealCustomRequest): Promise<MealLog> => {
    const response = await api.post<MealLog>('/logs/meal/custom', data);
    return response.data;
  },

  getTodayMeals: async (): Promise<MealLog[]> => {
    const response = await api.get<MealLog[]>('/logs/meals/today');
    return response.data;
  },

  logWater: async (data: WaterLogRequest): Promise<WaterLog> => {
    const response = await api.post<WaterLog>('/logs/water', data);
    return response.data;
  },

  getWaterToday: async (): Promise<WaterToday> => {
    const response = await api.get<WaterToday>('/logs/water/today');
    return response.data;
  },
};

export default logsApi;
