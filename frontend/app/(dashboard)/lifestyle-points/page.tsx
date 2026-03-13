'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  Trophy,
  Dumbbell,
  Utensils,
  Brain,
  Droplets,
  Moon,
  Clock,
  Sparkles,
  RefreshCw,
  Info,
} from 'lucide-react';
import Link from 'next/link';
import { lifestylePointsApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  ProgressBar,
} from '@/components/ui';
import { LineChart, CircularProgress } from '@/components/charts';
import { cn } from '@/lib/utils';

const POINT_CATEGORIES = [
  { id: 'exercise_score', label: 'Workout', icon: <Dumbbell className="w-5 h-5" />, color: '#F97316', max: 20 },
  { id: 'diet_score', label: 'Nutrition', icon: <Utensils className="w-5 h-5" />, color: '#10B981', max: 20 },
  { id: 'hydration_score', label: 'Hydration', icon: <Droplets className="w-5 h-5" />, color: '#3B82F6', max: 20 },
  { id: 'sleep_score', label: 'Sleep', icon: <Moon className="w-5 h-5" />, color: '#EC4899', max: 20 },
  { id: 'stress_score', label: 'Stress', icon: <Brain className="w-5 h-5" />, color: '#A855F7', max: 20 },
  { id: 'timing_score', label: 'Timing', icon: <Clock className="w-5 h-5" />, color: '#14B8A6', max: 20 },
  { id: 'consistency_bonus', label: 'Consistency', icon: <Sparkles className="w-5 h-5" />, color: '#EAB308', max: 5 },
];

export default function LifestylePointsPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();

  const { data: todayPoints, isLoading } = useQuery({
    queryKey: ['lifestylePoints', 'today'],
    queryFn: lifestylePointsApi.getToday,
  });

  const { data: history } = useQuery({
    queryKey: ['lifestylePoints', 'history'],
    queryFn: () => lifestylePointsApi.getHistory(30),
  });

  const recomputeMutation = useMutation({
    mutationFn: lifestylePointsApi.recompute,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Points recalculated!' });
    },
  });

  const totalPoints = todayPoints?.total || 0;
  const pointsBreakdown: Record<string, number> = todayPoints?.breakdown || {};

  // Prepare chart data
  const chartData = history?.map((day: any, i: number) => ({
    label: new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' }),
    value: day.total || 0,
  })) || [];

  // Calculate streak
  const streak = history?.reduce((count: number, day: any, i: number) => {
    if (i === 0 || (day.total || 0) >= 50) return count + 1;
    return 0;
  }, 0) || 0;

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-64 skeleton rounded-xl" />
          <div className="h-64 skeleton rounded-xl" />
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionHeading
            title="Lifestyle Points"
            subtitle="Track your daily healthy habits"
            className="mb-0"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => recomputeMutation.mutate()}
            loading={recomputeMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Recalculate
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main score */}
          <GlowCard className="lg:col-span-2">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="flex-shrink-0">
                <CircularProgress
                  value={totalPoints}
                  max={100}
                  size={180}
                  strokeWidth={16}
                  color="#14B8A6"
                  label="points"
                />
              </div>
              <div className="flex-1 w-full">
                <h3 className="text-lg font-semibold text-text-primary mb-1">Today's Score</h3>
                <p className="text-text-secondary mb-4">
                  {totalPoints >= 80
                    ? 'Outstanding! Keep up the great work!'
                    : totalPoints >= 50
                    ? 'Good progress! A few more habits to hit your goal.'
                    : 'Get started with your healthy habits for today!'}
                </p>
                
                {/* Categories */}
                <div className="space-y-3">
                  {POINT_CATEGORIES.map((cat) => {
                    const points = pointsBreakdown[cat.id] || 0;
                    const percentage = (points / cat.max) * 100;
                    return (
                      <div key={cat.id} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${cat.color}20` }}>
                          <span style={{ color: cat.color }}>{cat.icon}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-text-secondary">{cat.label}</span>
                            <span className="text-text-primary font-medium">{points}/{cat.max}</span>
                          </div>
                          <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                            <motion.div
                              className="h-full rounded-full"
                              style={{ backgroundColor: cat.color }}
                              initial={{ width: 0 }}
                              animate={{ width: `${percentage}%` }}
                              transition={{ duration: 0.8, ease: 'easeOut' }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </GlowCard>

          {/* Streak & stats */}
          <div className="space-y-4">
            <GlowCard>
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-yellow-500/10 flex items-center justify-center">
                  <Trophy className="w-7 h-7 text-yellow-400" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Current Streak</p>
                  <div className="flex items-baseline gap-1">
                    <AnimatedNumber value={streak} className="text-3xl font-bold text-text-primary" />
                    <span className="text-text-muted">days</span>
                  </div>
                </div>
              </div>
            </GlowCard>

            <GlowCard>
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-brand-teal/10 flex items-center justify-center">
                  <TrendingUp className="w-7 h-7 text-brand-teal" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Weekly Average</p>
                  <div className="flex items-baseline gap-1">
                    <AnimatedNumber
                      value={history && history.length > 0 
                        ? (history.slice(0, 7).reduce((sum: number, d: any) => sum + (d.points || d.total || 0), 0) / Math.min(history.length, 7)) 
                        : 0}
                      className="text-3xl font-bold text-text-primary"
                    />
                    <span className="text-text-muted">pts</span>
                  </div>
                </div>
              </div>
            </GlowCard>

            {/* How it works */}
            <GlowCard className="p-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-brand-teal flex-shrink-0 mt-0.5" />
                <div className="text-sm text-text-secondary">
                  <p className="font-medium text-text-primary mb-1">How it works</p>
                  <p>
                    Earn points by completing healthy activities each day. Aim for 100 points to maximize your health benefits!
                  </p>
                </div>
              </div>
            </GlowCard>
          </div>
        </div>

        {/* History chart */}
        <GlowCard>
          <SectionHeading title="30-Day History" subtitle="Your lifestyle points over time" className="mb-4" />
          {chartData.length > 0 ? (
            <LineChart
              data={chartData}
              height={250}
              showGrid
              color="#14B8A6"
            />
          ) : (
            <div className="h-[250px] flex items-center justify-center text-text-muted">
              No history data yet
            </div>
          )}
        </GlowCard>
      </div>
    </PageTransition>
  );
}
