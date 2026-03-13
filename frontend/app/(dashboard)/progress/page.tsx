'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Scale,
  TrendingUp,
  TrendingDown,
  Target,
  Calendar,
  Plus,
  Activity,
} from 'lucide-react';
import { progressApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  Modal,
  Tabs,
} from '@/components/ui';
import { LineChart, CircularProgress } from '@/components/charts';
import { NumberStepper } from '@/components/forms';
import { cn, formatDate } from '@/lib/utils';
import type { WeightLog, TrendPoint } from '@/lib/types';

export default function ProgressPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  const [activeTab, setActiveTab] = useState('weight');
  const [showLogModal, setShowLogModal] = useState(false);
  const [newWeight, setNewWeight] = useState(70);

  const { data: weightHistory } = useQuery({
    queryKey: ['progress', 'weight'],
    queryFn: () => progressApi.getWeightHistory(),
  });

  const { data: goalProgress } = useQuery({
    queryKey: ['progress', 'goals'],
    queryFn: progressApi.getGoalProgress,
  });

  const { data: lifestylePointsTrend } = useQuery({
    queryKey: ['progress', 'lifestylePoints'],
    queryFn: () => progressApi.getLifestylePointsTrend(30),
  });

  const { data: platformAverage } = useQuery({
    queryKey: ['progress', 'platformAverage'],
    queryFn: progressApi.getPlatformAverage,
  });

  const logWeightMutation = useMutation({
    mutationFn: (weight: number) => progressApi.logWeight({ weight_kg: weight }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['progress'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Weight logged!' });
      setShowLogModal(false);
    },
  });

  // Process weight data for chart
  const weightChartData = Array.isArray(weightHistory) ? weightHistory.map((entry: WeightLog) => ({
    label: formatDate(entry.date),
    value: entry.weight_kg,
  })) : [];

  // Calculate weight change
  const currentWeight = Array.isArray(weightHistory) ? (weightHistory[0]?.weight_kg || 0) : 0;
  const previousWeight = Array.isArray(weightHistory) ? (weightHistory[1]?.weight_kg || currentWeight) : currentWeight;
  const weightChange = currentWeight - previousWeight;
  const targetWeight = goalProgress?.target_weight || currentWeight;
  const weightToGoal = currentWeight - targetWeight;

  // Lifestyle points chart
  const lifestyleChartData = lifestylePointsTrend?.map((entry: TrendPoint) => ({
    label: formatDate(entry.date),
    value: entry.value || entry.total || 0,
  })) || [];

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Progress"
          subtitle="Track your fitness journey"
        />

        <Tabs
          tabs={[
            { id: 'weight', label: 'Weight' },
            { id: 'goals', label: 'Goals' },
            { id: 'activity', label: 'Activity' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {activeTab === 'weight' && (
          <div className="space-y-6">
            {/* Current weight cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <GlowCard>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-secondary mb-1">Current Weight</p>
                    <div className="flex items-baseline gap-1">
                      <AnimatedNumber value={currentWeight} decimals={1} className="text-3xl font-bold text-text-primary" />
                      <span className="text-text-muted">kg</span>
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-brand-teal/10 flex items-center justify-center">
                    <Scale className="w-6 h-6 text-brand-teal" />
                  </div>
                </div>
                <div className="mt-4">
                  <Button
                    onClick={() => {
                      setNewWeight(currentWeight || 70);
                      setShowLogModal(true);
                    }}
                    className="w-full"
                    icon={<Plus className="w-4 h-4" />}
                  >
                    Log Weight
                  </Button>
                </div>
              </GlowCard>

              <GlowCard>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-secondary mb-1">Change</p>
                    <div className="flex items-baseline gap-1">
                      <span className={cn(
                        'text-3xl font-bold',
                        weightChange < 0 ? 'text-risk-low' : weightChange > 0 ? 'text-risk-high' : 'text-text-primary'
                      )}>
                        {weightChange > 0 ? '+' : ''}{weightChange.toFixed(1)}
                      </span>
                      <span className="text-text-muted">kg</span>
                    </div>
                  </div>
                  <div className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center',
                    weightChange < 0 ? 'bg-risk-low/10' : weightChange > 0 ? 'bg-risk-high/10' : 'bg-bg-elevated'
                  )}>
                    {weightChange < 0 ? (
                      <TrendingDown className="w-6 h-6 text-risk-low" />
                    ) : (
                      <TrendingUp className="w-6 h-6 text-risk-high" />
                    )}
                  </div>
                </div>
                <p className="mt-3 text-xs text-text-muted">Since last weigh-in</p>
              </GlowCard>

              <GlowCard>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-text-secondary mb-1">To Goal</p>
                    <div className="flex items-baseline gap-1">
                      <AnimatedNumber 
                        value={Math.abs(weightToGoal)} 
                        decimals={1} 
                        className={cn(
                          'text-3xl font-bold',
                          weightToGoal <= 0 ? 'text-risk-low' : 'text-text-primary'
                        )}
                      />
                      <span className="text-text-muted">kg</span>
                    </div>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center">
                    <Target className="w-6 h-6 text-sky-500" />
                  </div>
                </div>
                <p className="mt-3 text-xs text-text-muted">Target: {targetWeight} kg</p>
              </GlowCard>
            </div>

            {/* Weight chart */}
            <GlowCard>
              <SectionHeading title="Weight History" subtitle="Your weight over time" className="mb-4" />
              {weightChartData.length > 0 ? (
                <LineChart
                  data={weightChartData}
                  height={300}
                  showGrid
                  color="#A855F7"
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-text-muted">
                  No weight data yet. Start logging your weight!
                </div>
              )}
            </GlowCard>
          </div>
        )}

        {activeTab === 'goals' && (
          <div className="space-y-6">
            <GlowCard>
              <SectionHeading title="Goal Progress" subtitle="Your overall fitness goals" className="mb-6" />
              
              {goalProgress ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Weight goal */}
                  <div className="flex items-center gap-4">
                    <CircularProgress
                      value={Math.max(0, 100 - (Math.abs(weightToGoal) / Math.abs((goalProgress.start_weight || currentWeight) - targetWeight)) * 100)}
                      size={100}
                      strokeWidth={10}
                      color="#A855F7"
                    />
                    <div>
                      <h4 className="font-semibold text-text-primary">Weight Goal</h4>
                      <p className="text-sm text-text-secondary">
                        {currentWeight.toFixed(1)}kg → {targetWeight.toFixed(1)}kg
                      </p>
                      <p className="text-sm text-text-muted">
                        {Math.abs(weightToGoal).toFixed(1)}kg remaining
                      </p>
                    </div>
                  </div>

                  {/* Goal progress */}
                  <div className="flex items-center gap-4">
                    <CircularProgress
                      value={goalProgress.percent || 0}
                      size={100}
                      strokeWidth={10}
                      color="#F97316"
                    />
                    <div>
                      <h4 className="font-semibold text-text-primary">{goalProgress.goal || 'Overall Progress'}</h4>
                      <p className="text-sm text-text-secondary">
                        {goalProgress.detail || 'Keep up the good work!'}
                      </p>
                      <p className="text-sm text-text-muted">
                        {goalProgress.percent || 0}% complete
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-text-muted">
                  No goal data available
                </div>
              )}
            </GlowCard>
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="space-y-6">
            {/* Platform comparison */}
            <GlowCard>
              <div className="flex items-center gap-4 mb-6">
                <Activity className="w-6 h-6 text-brand-teal" />
                <div>
                  <h3 className="font-semibold text-text-primary">Lifestyle Points Trend</h3>
                  <p className="text-sm text-text-secondary">Your activity compared to platform average</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-4 rounded-lg bg-bg-elevated text-center">
                  <AnimatedNumber 
                    value={lifestylePointsTrend && lifestylePointsTrend.length > 0 
                      ? lifestylePointsTrend.reduce((sum: number, d: any) => sum + (d.points || d.total || 0), 0) / lifestylePointsTrend.length 
                      : 0}
                    className="text-2xl font-bold text-brand-teal"
                  />
                  <p className="text-sm text-text-muted mt-1">Your Average</p>
                </div>
                <div className="p-4 rounded-lg bg-bg-elevated text-center">
                  <AnimatedNumber 
                    value={platformAverage?.avg_lifestyle_points || 0}
                    className="text-2xl font-bold text-text-secondary"
                  />
                  <p className="text-sm text-text-muted mt-1">Platform Average</p>
                </div>
              </div>

              {lifestyleChartData.length > 0 ? (
                <LineChart
                  data={lifestyleChartData}
                  height={250}
                  showGrid
                  color="#14B8A6"
                />
              ) : (
                <div className="h-[250px] flex items-center justify-center text-text-muted">
                  No activity data yet
                </div>
              )}
            </GlowCard>
          </div>
        )}

        {/* Log weight modal */}
        <Modal
          isOpen={showLogModal}
          onClose={() => setShowLogModal(false)}
          title="Log Weight"
          size="sm"
        >
          <div className="space-y-6">
            <div className="flex justify-center">
              <NumberStepper
                value={newWeight}
                onChange={setNewWeight}
                min={30}
                max={250}
                step={0.1}
                unit=" kg"
                size="lg"
              />
            </div>
            <Button
              className="w-full"
              onClick={() => logWeightMutation.mutate(newWeight)}
              loading={logWeightMutation.isPending}
            >
              Save Weight
            </Button>
          </div>
        </Modal>
      </div>
    </PageTransition>
  );
}
