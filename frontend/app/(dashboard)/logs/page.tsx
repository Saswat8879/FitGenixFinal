'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import {
  Utensils,
  Droplets,
  Search,
  Plus,
  Check,
  X,
  Trash2,
} from 'lucide-react';
import { logsApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  Tabs,
  Modal,
  Input,
  ProgressBar,
} from '@/components/ui';
import { NumberStepper, TileSelect } from '@/components/forms';
import { useDebounce } from '@/hooks';
import { cn, MEAL_SLOTS, roundCalories } from '@/lib/utils';

export default function LogsPage() {
  const searchParams = useSearchParams();
  const initialTab = searchParams.get('tab') || 'meals';
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  
  const [activeTab, setActiveTab] = useState(initialTab);
  const [showMealModal, setShowMealModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMealSlot, setSelectedMealSlot] = useState('breakfast');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedFood, setSelectedFood] = useState<any>(null);
  const [portionSize, setPortionSize] = useState(1);
  const [waterAmount, setWaterAmount] = useState(250);

  const debouncedSearch = useDebounce(searchQuery, 300);

  const { data: todayMeals } = useQuery({
    queryKey: ['meals', 'today'],
    queryFn: logsApi.getTodayMeals,
  });

  const { data: waterToday } = useQuery({
    queryKey: ['water', 'today'],
    queryFn: logsApi.getWaterToday,
  });

  // Search for food
  const searchMutation = useMutation({
    mutationFn: (query: string) => logsApi.searchMeal({ query }),
    onSuccess: (data) => {
      setSearchResults(data || []);
    },
  });

  // Log meal
  const logMealMutation = useMutation({
    mutationFn: (data: { name: string; meal_slot: string; portion_g: number; calories: number; protein_g?: number; carbs_g?: number; fat_g?: number }) =>
      logsApi.confirmMeal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] });
      queryClient.invalidateQueries({ queryKey: ['diet'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Meal logged!' });
      setShowMealModal(false);
      setSelectedFood(null);
      setSearchQuery('');
      setSearchResults([]);
    },
  });

  // Log water
  const logWaterMutation = useMutation({
    mutationFn: (ml: number) => logsApi.logWater({ amount_ml: ml }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['water'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Water logged!' });
    },
  });

  // Custom meal
  const customMealMutation = useMutation({
    mutationFn: (data: any) => logsApi.customMeal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meals'] });
      queryClient.invalidateQueries({ queryKey: ['diet'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Custom meal logged!' });
      setShowMealModal(false);
    },
  });

  const handleSearch = () => {
    if (debouncedSearch.length >= 2) {
      searchMutation.mutate(debouncedSearch);
    }
  };

  const totalCalories = todayMeals?.reduce((sum: number, m: any) => sum + (m.calories || 0), 0) || 0;
  const waterTotal = waterToday?.total_ml || 0;
  const waterTarget = 2500;
  const waterPercentage = Math.min((waterTotal / waterTarget) * 100, 100);

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Daily Logs"
          subtitle="Track your meals and water intake"
        />

        <Tabs
          tabs={[
            { id: 'meals', label: 'Meals' },
            { id: 'water', label: 'Water' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {activeTab === 'meals' && (
          <div className="space-y-6">
            {/* Summary card */}
            <GlowCard>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-text-secondary mb-1">Today's Calories</p>
                  <div className="flex items-baseline gap-2">
                    <AnimatedNumber value={totalCalories} className="text-3xl font-bold text-text-primary" />
                    <span className="text-text-muted">kcal</span>
                  </div>
                </div>
                <Button
                  onClick={() => setShowMealModal(true)}
                  icon={<Plus className="w-4 h-4" />}
                >
                  Log Meal
                </Button>
              </div>
            </GlowCard>

            {/* Meal list */}
            <div className="space-y-3">
              {MEAL_SLOTS.map((slot) => {
                const slotMeals = todayMeals?.filter((m: any) => m.meal_slot === slot.value) || [];
                return (
                  <GlowCard key={slot.value} className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-text-primary">{slot.label}</h3>
                      <span className="text-sm text-text-muted">
                        {roundCalories(slotMeals.reduce((sum: number, m: any) => sum + (m.calories || 0), 0))} kcal
                      </span>
                    </div>
                    {slotMeals.length > 0 ? (
                      <div className="space-y-2">
                        {slotMeals.map((meal: any) => (
                          <div
                            key={meal.id}
                            className="flex items-center justify-between p-2 rounded-lg bg-bg-elevated"
                          >
                            <div>
                              <p className="text-sm font-medium text-text-primary">{meal.food_name}</p>
                              <p className="text-xs text-text-muted">{roundCalories(meal.calories)} kcal</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-text-muted text-center py-2">
                        No meals logged
                      </p>
                    )}
                  </GlowCard>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === 'water' && (
          <div className="space-y-6">
            {/* Water progress */}
            <GlowCard>
              <div className="flex flex-col items-center py-6">
                <div className="relative w-40 h-40 mb-6">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="80"
                      cy="80"
                      r="70"
                      fill="none"
                      stroke="#1E293B"
                      strokeWidth="12"
                    />
                    <motion.circle
                      cx="80"
                      cy="80"
                      r="70"
                      fill="none"
                      stroke="#3B82F6"
                      strokeWidth="12"
                      strokeLinecap="round"
                      strokeDasharray={2 * Math.PI * 70}
                      initial={{ strokeDashoffset: 2 * Math.PI * 70 }}
                      animate={{ strokeDashoffset: 2 * Math.PI * 70 * (1 - waterPercentage / 100) }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <Droplets className="w-8 h-8 text-blue-400 mb-1" />
                    <AnimatedNumber value={waterTotal} className="text-2xl font-bold text-text-primary" />
                    <span className="text-sm text-text-muted">/ {waterTarget} ml</span>
                  </div>
                </div>

                <div className="flex gap-3">
                  {[250, 500, 750].map((amount) => (
                    <Button
                      key={amount}
                      variant="outline"
                      onClick={() => logWaterMutation.mutate(amount)}
                      loading={logWaterMutation.isPending}
                    >
                      +{amount}ml
                    </Button>
                  ))}
                </div>

                <div className="flex items-center gap-3 mt-6 w-full max-w-xs">
                  <NumberStepper
                    value={waterAmount}
                    onChange={setWaterAmount}
                    min={50}
                    max={2000}
                    step={50}
                    unit="ml"
                  />
                  <Button
                    onClick={() => logWaterMutation.mutate(waterAmount)}
                    loading={logWaterMutation.isPending}
                    icon={<Plus className="w-4 h-4" />}
                  >
                    Add
                  </Button>
                </div>
              </div>
            </GlowCard>

            {/* Water logs */}
            {waterToday?.logs && waterToday.logs.length > 0 && (
              <GlowCard>
                <h3 className="font-semibold text-text-primary mb-4">Today's Water Logs</h3>
                <div className="space-y-2">
                  {waterToday.logs.map((log: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-bg-elevated">
                      <div className="flex items-center gap-2">
                        <Droplets className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-text-primary">{log.amount_ml} ml</span>
                      </div>
                      <span className="text-xs text-text-muted">{log.time}</span>
                    </div>
                  ))}
                </div>
              </GlowCard>
            )}
          </div>
        )}

        {/* Meal search modal */}
        <Modal
          isOpen={showMealModal}
          onClose={() => {
            setShowMealModal(false);
            setSelectedFood(null);
            setSearchQuery('');
            setSearchResults([]);
          }}
          title="Log Meal"
          size="lg"
        >
          <div className="space-y-4">
            {!selectedFood ? (
              <>
                <TileSelect
                  label="Meal Type"
                  options={[...MEAL_SLOTS]}
                  value={selectedMealSlot}
                  onChange={(v) => setSelectedMealSlot(v as string)}
                  columns={4}
                />

                <div className="flex gap-2">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search for food..."
                    icon={<Search className="w-4 h-4" />}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <Button onClick={handleSearch} loading={searchMutation.isPending}>
                    Search
                  </Button>
                </div>

                {searchResults.length > 0 && (
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {searchResults.map((food: any) => (
                      <button
                        key={food.id}
                        onClick={() => setSelectedFood(food)}
                        className="w-full flex items-center justify-between p-3 rounded-lg bg-bg-elevated hover:bg-bg-border transition-colors text-left"
                      >
                        <div>
                          <p className="font-medium text-text-primary">{food.name}</p>
                          <p className="text-sm text-text-muted">
                            {roundCalories(food.calories)} kcal per {food.serving_size}{food.serving_unit}
                          </p>
                        </div>
                        <Plus className="w-4 h-4 text-text-muted" />
                      </button>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-bg-elevated">
                  <h4 className="font-semibold text-text-primary">{selectedFood.name}</h4>
                  <p className="text-sm text-text-muted">
                    {roundCalories(selectedFood.calories * portionSize)} kcal for {portionSize} serving(s)
                  </p>
                </div>

                <NumberStepper
                  label="Portions"
                  value={portionSize}
                  onChange={setPortionSize}
                  min={0.5}
                  max={10}
                  step={0.5}
                />

                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setSelectedFood(null)}
                  >
                    Back
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => logMealMutation.mutate({
                      name: selectedFood.name,
                      meal_slot: selectedMealSlot,
                      portion_g: 100 * portionSize,
                      calories: Math.round(selectedFood.calories * portionSize),
                      protein_g: selectedFood.protein_g ? Math.round(selectedFood.protein_g * portionSize) : undefined,
                      carbs_g: selectedFood.carbs_g ? Math.round(selectedFood.carbs_g * portionSize) : undefined,
                      fat_g: selectedFood.fat_g ? Math.round(selectedFood.fat_g * portionSize) : undefined,
                    })}
                    loading={logMealMutation.isPending}
                    icon={<Check className="w-4 h-4" />}
                  >
                    Log Meal
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Modal>
      </div>
    </PageTransition>
  );
}
