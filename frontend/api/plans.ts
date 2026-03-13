import api from './axios';
import { Workout, WorkoutFeedback, DietPlan } from '@/lib/types';

export const plansApi = {
  getTodayWorkout: async (): Promise<Workout> => {
    const response = await api.get<Workout>('/plans/workout/today');
    return response.data;
  },

  getWorkout: async (workoutId: number): Promise<Workout> => {
    const response = await api.get<Workout>(`/plans/workout/${workoutId}`);
    return response.data;
  },

  completeWorkout: async (workoutId: number): Promise<Workout> => {
    const response = await api.post<Workout>(`/plans/workout/${workoutId}/complete`);
    return response.data;
  },

  submitWorkoutFeedback: async (workoutId: number, feedback: Omit<WorkoutFeedback, 'workout_id'>): Promise<Workout> => {
    const response = await api.post<Workout>(`/plans/workout/${workoutId}/feedback`, {
      workout_id: workoutId,
      ...feedback,
    });
    return response.data;
  },

  getTodayDiet: async (): Promise<DietPlan> => {
    const response = await api.get<DietPlan>('/plans/diet/today');
    return response.data;
  },

  getDietPlan: async (planId: number): Promise<DietPlan> => {
    const response = await api.get<DietPlan>(`/plans/diet/${planId}`);
    return response.data;
  },

  regeneratePlans: async (workout: boolean, diet: boolean): Promise<{ message: string; workout_id?: number; diet_plan_id?: number }> => {
    const response = await api.post<{ message: string; workout_id?: number; diet_plan_id?: number }>('/plans/regenerate', {
      workout,
      diet,
    });
    return response.data;
  },
};

export default plansApi;
