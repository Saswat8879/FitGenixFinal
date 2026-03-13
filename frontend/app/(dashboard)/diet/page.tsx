'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Utensils,
  ChevronDown,
  ChevronUp,
  Plus,
  Check,
  RefreshCw,
  Flame,
  Apple,
  Beef,
  Wheat,
  Droplet,
} from 'lucide-react';
import { plansApi, logsApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  Tabs,
} from '@/components/ui';
import { CircularProgress, DonutChart } from '@/components/charts';
import { cn, roundCalories } from '@/lib/utils';
import type { MealItem, FoodItem } from '@/lib/types';

const MEAL_SLOTS = [
  { id: 'breakfast', label: 'Breakfast', time: '7:00 - 9:00 AM' },
  { id: 'lunch', label: 'Lunch', time: '12:00 - 2:00 PM' },
  { id: 'dinner', label: 'Dinner', time: '6:00 - 8:00 PM' },
  { id: 'snack', label: 'Snacks', time: 'Any time' },
];

export default function DietPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  const [activeTab, setActiveTab] = useState('today');
  const [expandedMeal, setExpandedMeal] = useState<string | null>('breakfast');

  const { data: dietPlan, isLoading } = useQuery({
    queryKey: ['diet', 'today'],
    queryFn: plansApi.getTodayDiet,
  });

  const { data: todayMeals } = useQuery({
    queryKey: ['meals', 'today'],
    queryFn: logsApi.getTodayMeals,
  });

  const logMealMutation = useMutation({
    mutationFn: ({
      dietPlanId,
      foodId,
      mealSlot,
      portionG,
      foodName,
      calories,
      proteinG,
      carbsG,
      fatG,
      fiberG,
      sodiumMg,
      sugarG,
      saturatedFatG,
    }: {
      dietPlanId: number;
      foodId?: number;
      mealSlot: string;
      portionG?: number;
      foodName?: string;
      calories?: number;
      proteinG?: number;
      carbsG?: number;
      fatG?: number;
      fiberG?: number;
      sodiumMg?: number;
      sugarG?: number;
      saturatedFatG?: number;
    }) =>
      logsApi.mealFromPlan({
        diet_plan_id: dietPlanId,
        food_id: foodId,
        food_name: foodName,
        meal_slot: mealSlot,
        portion_g: portionG,
        calories,
        protein_g: proteinG,
        carbs_g: carbsG,
        fat_g: fatG,
        fiber_g: fiberG,
        sodium_mg: sodiumMg,
        sugar_g: sugarG,
        saturated_fat_g: saturatedFatG,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Meal logged successfully!' });
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: () => plansApi.regeneratePlans(false, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diet'] });
      addToast({ type: 'success', message: 'New diet plan generated!' });
    },
  });

  // Get logged meal IDs
  const loggedMealKeys = new Set(
    (todayMeals || []).map((m: any) => `${m.meal_slot}:${(m.food_name || '').toLowerCase()}`)
  );

  // Group meals by slot - meals is Record<string, MealSlot> where MealSlot has items: FoodItem[]
  const getMealsForSlot = (slotId: string): FoodItem[] => {
    const slot = dietPlan?.meals?.[slotId] as any;
    if (!slot) return [];
    if (Array.isArray(slot)) return slot as FoodItem[];
    if (Array.isArray(slot.items)) return slot.items as FoodItem[];
    return [];
  };

  const planFiber = MEAL_SLOTS.reduce((sum, slot) => {
    return sum + getMealsForSlot(slot.id).reduce((slotSum: number, meal: any) => slotSum + (meal.fiber_g || 0), 0);
  }, 0);

  const loggedTotals = {
    calories: (todayMeals || []).reduce((sum: number, m: any) => sum + (m.calories || 0), 0),
    protein: (todayMeals || []).reduce((sum: number, m: any) => sum + (m.protein || 0), 0),
    carbs: (todayMeals || []).reduce((sum: number, m: any) => sum + (m.carbs || 0), 0),
    fat: (todayMeals || []).reduce((sum: number, m: any) => sum + (m.fat || 0), 0),
    fiber: (todayMeals || []).reduce((sum: number, m: any) => sum + (m.fiber || 0), 0),
  };

  // If any meal is logged today, show consumed macros from logs; otherwise show planned macros.
  const hasLoggedMeals = (todayMeals?.length || 0) > 0;
  const totals = hasLoggedMeals
    ? loggedTotals
    : {
        calories: dietPlan?.total_calories || 0,
        protein: dietPlan?.total_protein || 0,
        carbs: dietPlan?.total_carbs || 0,
        fat: dietPlan?.total_fat || 0,
        fiber: dietPlan?.total_fiber_g || planFiber || 0,
      };

  const targets = {
    calories: dietPlan?.calorie_target || 2000,
    protein: dietPlan?.protein_target_g || 120,
    carbs: dietPlan?.carbs_target_g || 200,
    fat: dietPlan?.fat_target_g || 60,
    fiber: dietPlan?.fiber_target_g || 30,
  };

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-48 skeleton rounded-xl" />
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 skeleton rounded-xl" />
          ))}
        </div>
      </PageTransition>
    );
  }

  if (!dietPlan) {
    return (
      <PageTransition>
        <div className="text-center py-12">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-bg-elevated flex items-center justify-center">
            <Utensils className="w-10 h-10 text-text-muted" />
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">No Diet Plan</h2>
          <p className="text-text-secondary mb-6">
            Your personalized diet plan hasn't been generated yet.
          </p>
          <Button
            onClick={() => regenerateMutation.mutate()}
            loading={regenerateMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Generate Diet Plan
          </Button>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionHeading
            title="Diet Plan"
            subtitle="Your personalized nutrition for today"
            className="mb-0"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => regenerateMutation.mutate()}
            loading={regenerateMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Regenerate
          </Button>
        </div>

        {/* Macro overview */}
        <GlowCard>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
            {/* Calories donut */}
            <div className="col-span-2 lg:col-span-1 flex flex-col items-center justify-center">
              <DonutChart
                data={[
                  { label: 'Consumed', value: roundCalories(totals.calories), color: '#14B8A6' },
                  { label: 'Remaining', value: roundCalories(Math.max(targets.calories - totals.calories, 0)), color: '#1E293B' },
                ]}
                size={140}
                innerRadius={45}
                outerRadius={65}
                centerValue={roundCalories(totals.calories)}
                centerLabel="kcal"
              />
              <p className="text-sm text-text-muted mt-2">
                of {roundCalories(targets.calories)} kcal
              </p>
              <p className="text-xs text-text-muted mt-1">
                {hasLoggedMeals ? 'based on today\'s logs' : 'based on today\'s plan'}
              </p>
            </div>

            {/* Macros */}
            {[
              { label: 'Protein', value: totals.protein, target: targets.protein, color: '#EF4444', icon: <Beef className="w-5 h-5" /> },
              { label: 'Carbs', value: totals.carbs, target: targets.carbs, color: '#F59E0B', icon: <Wheat className="w-5 h-5" /> },
              { label: 'Fat', value: totals.fat, target: targets.fat, color: '#3B82F6', icon: <Droplet className="w-5 h-5" /> },
              { label: 'Fiber', value: totals.fiber, target: targets.fiber, color: '#10B981', icon: <Apple className="w-5 h-5" /> },
            ].map((macro) => (
              <div key={macro.label} className="text-center">
                <div className="flex items-center justify-center gap-2 mb-3" style={{ color: macro.color }}>
                  {macro.icon}
                  <span className="text-sm font-medium text-text-secondary">{macro.label}</span>
                </div>
                <CircularProgress
                  value={macro.value}
                  max={macro.target}
                  size={80}
                  strokeWidth={6}
                  color={macro.color}
                  showValue={false}
                />
                <p className="mt-2 font-semibold text-text-primary">
                  <AnimatedNumber value={macro.value} className="text-text-primary" />g
                </p>
                <p className="text-xs text-text-muted">/ {macro.target}g</p>
              </div>
            ))}
          </div>
        </GlowCard>

        {/* Meals by slot */}
        <div className="space-y-4">
          {MEAL_SLOTS.map((slot) => {
            const meals = getMealsForSlot(slot.id);
            const isExpanded = expandedMeal === slot.id;
            const slotCalories = meals.reduce((sum: number, m: FoodItem) => sum + (m.calories || 0), 0);
            const loggedSlotMeals = (todayMeals || []).filter((m: any) => m.meal_slot === slot.id);
            const plannedNames = new Set(meals.map((m: FoodItem) => (m.food_name || m.name || '').toLowerCase()));
            const extraLoggedMeals = loggedSlotMeals.filter(
              (m: any) => !plannedNames.has(String(m.food_name || '').toLowerCase())
            );

            return (
              <motion.div
                key={slot.id}
                layout
                className="rounded-xl border bg-bg-card border-bg-border overflow-hidden"
              >
                <button
                  onClick={() => setExpandedMeal(isExpanded ? null : slot.id)}
                  className="w-full p-4 flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-bg-elevated flex items-center justify-center">
                      <Utensils className="w-6 h-6 text-brand-teal" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-text-primary">{slot.label}</h3>
                      <p className="text-sm text-text-muted">{slot.time}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold text-text-primary">
                        {roundCalories(slotCalories)} kcal
                      </p>
                      <p className="text-xs text-text-muted">
                        {meals.length} items
                      </p>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-text-muted" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-text-muted" />
                    )}
                  </div>
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 space-y-3">
                        {meals.length > 0 ? (
                          meals.map((meal: FoodItem, index: number) => {
                            const mealId = meal.food_id || meal.id || index;
                            const mealName = meal.food_name || meal.name || '';
                            const isLogged = loggedMealKeys.has(`${slot.id}:${mealName.toLowerCase()}`);
                            const canLog = !!mealName;
                            return (
                              <div
                                key={mealId}
                                className={cn(
                                  'flex items-center justify-between p-3 rounded-lg border',
                                  isLogged
                                    ? 'bg-risk-low/10 border-risk-low/30'
                                    : 'bg-bg-elevated border-bg-border'
                                )}
                              >
                                <div className="flex-1">
                                  <h4 className="font-medium text-text-primary">{mealName}</h4>
                                  <p className="text-sm text-text-muted">
                                    {meal.portion_size || meal.portion_g || 100}g • {roundCalories(meal.calories)} kcal
                                  </p>
                                  <div className="flex gap-3 mt-1 text-xs text-text-muted">
                                    <span>P: {meal.protein_g || 0}g</span>
                                    <span>C: {meal.carbs_g || 0}g</span>
                                    <span>F: {meal.fat_g || 0}g</span>
                                  </div>
                                </div>
                                <div>
                                  {isLogged ? (
                                    <div className="flex items-center gap-1 text-risk-low">
                                      <Check className="w-4 h-4" />
                                      <span className="text-sm">Logged</span>
                                    </div>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => logMealMutation.mutate({ 
                                        dietPlanId: dietPlan?.id || 0,
                                        foodId: meal.food_id,
                                        mealSlot: slot.id,
                                        portionG: meal.portion_g || 100,
                                        foodName: mealName,
                                        calories: meal.calories,
                                        proteinG: meal.protein_g,
                                        carbsG: meal.carbs_g,
                                        fatG: meal.fat_g,
                                        fiberG: (meal as any).fiber_g,
                                        sodiumMg: (meal as any).sodium_mg,
                                        sugarG: (meal as any).sugar_g,
                                        saturatedFatG: (meal as any).saturated_fat_g,
                                      })}
                                      disabled={!canLog}
                                      loading={logMealMutation.isPending}
                                      icon={<Plus className="w-4 h-4" />}
                                    >
                                      Log
                                    </Button>
                                  )}
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <div className="text-center py-4 text-text-muted">
                            No meals planned for this slot
                          </div>
                        )}

                        {extraLoggedMeals.length > 0 && (
                          <div className="pt-2 border-t border-bg-border space-y-2">
                            <p className="text-xs uppercase tracking-wide text-text-muted">Also Logged</p>
                            {extraLoggedMeals.map((meal: any) => (
                              <div key={`logged-${meal.id}`} className="flex items-center justify-between p-3 rounded-lg bg-risk-low/10 border border-risk-low/30">
                                <div>
                                  <h4 className="font-medium text-text-primary">{meal.food_name}</h4>
                                  <p className="text-sm text-text-muted">
                                    {meal.portion_g || 100}g • {roundCalories(meal.calories || 0)} kcal
                                  </p>
                                </div>
                                <div className="flex items-center gap-1 text-risk-low">
                                  <Check className="w-4 h-4" />
                                  <span className="text-sm">Logged</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </PageTransition>
  );
}
