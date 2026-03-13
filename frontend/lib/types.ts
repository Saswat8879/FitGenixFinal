// Auth Types
export interface User {
  id: number;
  email: string;
  name: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  cluster_id?: number;
  cluster_archetype?: string;
  is_admin: boolean;
  onboarding_completed?: boolean;
  created_at?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRegister {
  email: string;
  password: string;
  name: string;
  first_name?: string;
  last_name?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface ForgotPasswordResponse {
  message: string;
  reset_token?: string;
  reset_url?: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

// Onboarding Types
export interface OnboardingSurvey {
  age: number;
  sex: string;
  height_cm: number;
  weight_kg: number;
  target_weight_kg?: number;
  country?: string;
  goal: string;
  diet_type: string;
  coaching_style?: string;
  activity_level?: string;
  work_style?: string;
  time_available_min?: number;
  cuisine_preference?: string;
  equipment?: string[];
  available_equipment?: string[];
  sleep_hours_avg?: number;
  stress_level?: number;
  workout_days_per_week?: number;
  workout_minutes_per_day?: number;
  medical_conditions?: string[];
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
  preferred_notifications?: boolean;
}

export interface OnboardingResponse {
  message: string;
  cluster_id?: number;
  cluster_archetype?: string;
  diabetes_risk?: string;
  workout_id?: number;
  diet_plan_id?: number;
}

// Profile Types
export interface Profile {
  user_id: number;
  name: string;
  email: string;
  age?: number;
  sex?: string;
  height_cm?: number;
  weight_kg?: number;
  goal?: string;
  diet_type?: string;
  equipment?: string[];
  time_available_min?: number;
  coaching_style?: string;
  country?: string;
  cuisine_preference?: string;
  activity_level?: string;
  work_style?: string;
  preferred_notifications?: boolean;
  cluster_archetype?: string;
  conditions?: Record<string, boolean>;
  updated_at?: string;
  // Stats for profile page
  workouts_completed?: number;
  streak?: number;
  total_points?: number;
}

// Dashboard Types
export interface DashboardData {
  user_name: string;
  cluster_archetype?: string;
  bmi?: number;
  diabetes_risk?: string;
  diabetes_risk_score?: number;
  cvd_risk_score?: number;
  lifestyle_points: number;
  lifestyle_breakdown?: Record<string, number>;
  workout_status: string;
  workout_exercise_count: number;
  diet_plan_calories?: number;
  diet_adherence?: number;
  // Additional metrics properties used in dashboard
  metrics?: {
    diabetes_risk_score?: number;
    cvd_risk_score?: number;
  };
  calories_consumed?: number;
  calorie_target?: number;
  water_ml?: number;
  water_target_ml?: number;
  weight_kg?: number;
  stress_level?: number;
  // Nested workout info
  workout?: {
    name?: string;
    exercises_count?: number;
    duration_minutes?: number;
    calories_burn?: number;
  };
  // Nested diet info
  diet?: {
    meals_logged?: number;
    meals_planned?: number;
    protein_g?: number;
    protein_target?: number;
    carbs_g?: number;
    carbs_target?: number;
    fat_g?: number;
    fat_target?: number;
  };
}

export interface DashboardTrends {
  lifestyle_points: TrendPoint[];
  calories: TrendPoint[];
  water?: TrendPoint[];
  weight?: TrendPoint[];
}

export interface TrendPoint {
  date: string;
  total?: number;
  value?: number;
}

// Plans Types
export interface Workout {
  id: number;
  date?: string;
  name?: string;
  description?: string;
  exercises: Exercise[];
  status: string;
  completed?: boolean;
  completed_at?: string;
  duration_minutes?: number;
  estimated_calories?: number;
  feedback?: WorkoutFeedback;
  source: string;
}

export interface Exercise {
  id?: number;
  name: string;
  sets?: number;
  reps?: number;
  body_part?: string;
  muscle_group?: string;
  difficulty?: string;
  equipment?: string;
  weight_kg?: number;
  rest_seconds?: number;
  target_muscles?: string[];
  instructions?: string;
}

export interface WorkoutFeedback {
  workout_id: number;
  completed: boolean;
  difficulty_rating?: number;
  rating?: number;
  notes?: string;
  exercises_completed?: { name: string; done: boolean }[];
}

export interface DietPlan {
  id: number;
  date?: string;
  meals: Record<string, MealSlot>;
  total_calories: number;
  total_protein: number;
  total_protein_g?: number;
  total_carbs: number;
  total_carbs_g?: number;
  total_fat: number;
  total_fat_g?: number;
  total_fiber_g?: number;
  total_sodium: number;
  adherence_score: number;
  source: string;
  calorie_target?: number;
  protein_target_g?: number;
  carbs_target_g?: number;
  fat_target_g?: number;
  fiber_target_g?: number;
  bmr?: number;
  tdee?: number;
}

export interface MealSlot {
  items: FoodItem[];
  calories: number;
}

export interface MealItem {
  id?: number;
  name: string;
  food_name?: string;
  portion_g: number;
  portion_size?: number;
  portion_unit?: string;
  calories: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  meal_slot?: string;
}

export interface FoodItem {
  id?: number;
  food_id?: number;
  name: string;
  food_name?: string;
  portion_g: number;
  portion_size?: number;
  portion_unit?: string;
  calories: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
}

// Logs Types
export interface MealSearchResult {
  name: string;
  source: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  food_id?: number;
}

export interface MealLog {
  id: number;
  food_name?: string;
  meal_slot: string;
  portion_g: number;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number;
  timestamp?: string;
  source: string;
}

export interface WaterLog {
  id: number;
  timestamp: string;
  amount_ml: number;
  source: string;
}

export interface WaterToday {
  total_ml: number;
  target_ml: number;
  log_count: number;
  logs?: WaterLog[];
}

// Lifestyle Types
export interface StressResult {
  stress_level: number;
  is_stressed: boolean;
  method: string;
  interventions: string[];
  recommendation?: string;
  timestamp?: string;
}

export interface LifestyleCheckin {
  mood?: number;
  energy_level?: number;
  anxiety_level?: number;
  sleep_hours?: number;
  sleep_quality?: number;
  stress_self_report?: number;
  hydration_ml?: number;
  sedentary_minutes?: number;
  posture_alert?: boolean;
}

export interface LifestyleCheckinOut {
  id: number;
  timestamp?: string;
  mood?: number;
  sleep_hours?: number;
  sleep_quality?: number;
  stress_level?: number;
  is_stressed?: boolean;
  hydration_ml?: number;
  sedentary_minutes?: number;
  stress_interventions?: string[];
  message?: string;
}

export interface Tips {
  tips: string[];
}

export interface PostureStatus {
  alert: boolean;
  sedentary_minutes: number;
  message: string;
  exercise?: {
    name: string;
    description: string;
  };
}

// Health Types
export interface HealthMetrics {
  bmi?: number;
  weight_kg?: number;
  diabetes_risk_score?: number;
  diabetes_risk_category?: string;
  cvd_risk_score?: number;
  stress_level?: number;
  resting_hr?: number;
  avg_daily_steps?: number;
  avg_active_minutes?: number;
  avg_sleep_hours?: number;
  timestamp?: string;
}

export interface RiskResult {
  risk_type: string;
  score?: number;
  category?: string;
  method: string;
}

// Progress Types
export interface WeightLog {
  date: string;
  weight_kg: number;
  bmi?: number;
}

export interface WeightLogResponse {
  id: number;
  weight_kg: number;
  bmi: number;
  timestamp: string;
  message: string;
}

export interface GoalProgress {
  goal: string;
  percent: number;
  detail?: string;
  start_weight?: number;
  current_weight?: number;
  target_weight?: number;
  risk_score?: number;
  avg_points?: number;
}

export interface PlatformAverage {
  avg_lifestyle_points: number;
  active_users: number;
}

// Lifestyle Points Types
export interface LifestylePoints {
  date: string;
  total: number;
  total_points?: number;
  breakdown: Record<string, number>;
}

// Chat Types
export interface ChatMessage {
  id: number;
  timestamp: string;
  role: 'user' | 'assistant';
  message: string;
}

export interface ChatResponse {
  response: string;
  retrieved_sources: string[];
  disclaimer?: string;
}

// Community Types
export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  name: string;
  weekly_steps: number;
  workouts_completed: number;
  streak: number;
  total_points: number;
}

export interface LeaderboardData {
  entries: LeaderboardEntry[];
  total: number;
}

export interface MyRank {
  rank?: number;
  total_points: number;
  weekly_steps: number;
  workouts_completed: number;
  streak: number;
  is_flagged: boolean;
  message?: string;
}

// Google Fit Types
export interface FitStatus {
  connected: boolean;
  expires_at?: string;
}

export interface FitConnectResponse {
  auth_url: string;
}

// Simulation Types
export interface SimulationResponse {
  simulation_type: string;
  data: Record<string, unknown>;
}

// Common Types
export type RiskLevel = 'low' | 'moderate' | 'high';

export interface ApiError {
  detail: string;
}
