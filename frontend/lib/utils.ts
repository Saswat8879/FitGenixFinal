import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number, decimals: number = 1): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function roundCalories(value: number | null | undefined): number {
  return Math.round(Number(value || 0));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function formatTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return formatDate(d);
}

export function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export function getRiskColor(level: 'low' | 'moderate' | 'high'): string {
  const colors = {
    low: 'text-risk-low bg-risk-low/10 border-risk-low/30',
    moderate: 'text-risk-moderate bg-risk-moderate/10 border-risk-moderate/30',
    high: 'text-risk-high bg-risk-high/10 border-risk-high/30',
  };
  return colors[level] || colors.low;
}

export function getBMICategory(bmi: number): { label: string; level: 'low' | 'moderate' | 'high' } {
  if (bmi < 18.5) return { label: 'Underweight', level: 'moderate' };
  if (bmi < 25) return { label: 'Normal', level: 'low' };
  if (bmi < 30) return { label: 'Overweight', level: 'moderate' };
  return { label: 'Obese', level: 'high' };
}

export function getRiskLevel(score: number): 'low' | 'moderate' | 'high' {
  if (score < 0.3) return 'low';
  if (score < 0.7) return 'moderate';
  return 'high';
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
}

export const MEAL_SLOTS = [
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snack', label: 'Snack' },
  { value: 'other', label: 'Other' },
] as const;

export const GOALS = [
  { value: 'lose_weight', label: 'Weight Loss', icon: 'TrendingDown' },
  { value: 'gain_muscle', label: 'Muscle Gain', icon: 'Dumbbell' },
  { value: 'maintain', label: 'Maintain', icon: 'Scale' },
  { value: 'manage_condition', label: 'Manage Condition', icon: 'Heart' },
] as const;

export const ACTIVITY_LEVELS = [
  { value: 'sedentary', label: 'Sedentary', description: 'Little to no exercise' },
  { value: 'lightly_active', label: 'Lightly Active', description: '1-3 days/week' },
  { value: 'moderately_active', label: 'Moderately Active', description: '3-5 days/week' },
  { value: 'very_active', label: 'Very Active', description: '6-7 days/week' },
] as const;

export const COACHING_STYLES = [
  { value: 'gentle', label: 'Gentle', description: 'Supportive and gradual' },
  { value: 'moderate', label: 'Moderate', description: 'Balanced approach' },
  { value: 'intense', label: 'Intense', description: 'Push for results' },
] as const;

export const DIET_TYPES = [
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'non_vegetarian', label: 'Non-Vegetarian' },
  { value: 'eggetarian', label: 'Eggetarian' },
] as const;

export const WORK_STYLES = [
  { value: 'desk_job', label: 'Desk Job' },
  { value: 'remote', label: 'Remote Work' },
  { value: 'field_work', label: 'Field Work' },
  { value: 'hybrid', label: 'Hybrid' },
  { value: 'student', label: 'Student' },
] as const;

export const EQUIPMENT_OPTIONS = [
  'None',
  'Dumbbells',
  'Barbell',
  'Resistance Bands',
  'Pull-up Bar',
  'Kettlebell',
  'Bench',
  'Treadmill',
  'Stationary Bike',
  'Yoga Mat',
] as const;

export const MEDICAL_CONDITIONS = [
  { field: 'type_2_diabetes', label: 'Type 2 Diabetes' },
  { field: 'pre_diabetes', label: 'Pre-Diabetes' },
  { field: 'hypertension', label: 'Hypertension' },
  { field: 'high_cholesterol', label: 'High Cholesterol' },
  { field: 'fatty_liver', label: 'Fatty Liver' },
  { field: 'obesity', label: 'Obesity' },
  { field: 'asthma_copd', label: 'Asthma / COPD' },
  { field: 'back_pain', label: 'Back Pain' },
  { field: 'knee_pain', label: 'Knee Pain' },
  { field: 'shoulder_pain', label: 'Shoulder Pain' },
  { field: 'family_history_diabetes', label: 'Family History of Diabetes' },
  { field: 'on_medication', label: 'Currently on Medication' },
  { field: 'doctor_supervised', label: 'Under Doctor Supervision' },
] as const;
