'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Flame,
  Droplets,
  Scale,
  TrendingUp,
  Heart,
  Brain,
  Dumbbell,
  Utensils,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';
import { dashboardApi, lifestylePointsApi, healthApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  RiskBadge,
  SkeletonLoader,
} from '@/components/ui';
import { CircularProgress, LineChart, SparkLine } from '@/components/charts';
import { cn, getRiskLevel, getGreeting, roundCalories } from '@/lib/utils';

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

export default function DashboardPage() {
  const { user } = useAuthStore();
  const greeting = getGreeting();

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getDashboard,
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: lifestylePoints } = useQuery({
    queryKey: ['lifestylePoints', 'today'],
    queryFn: lifestylePointsApi.getToday,
  });

  const { data: trends } = useQuery({
    queryKey: ['dashboard', 'trends'],
    queryFn: () => dashboardApi.getTrends(7),
  });

  if (dashboardLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-24 skeleton rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 skeleton rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-64 skeleton rounded-xl" />
          <div className="h-64 skeleton rounded-xl" />
        </div>
      </PageTransition>
    );
  }

  const diabetesRisk = getRiskLevel(dashboard?.metrics?.diabetes_risk_score || 0);
  const cvdRisk = getRiskLevel(dashboard?.metrics?.cvd_risk_score || 0);

  return (
    <PageTransition>
      <motion.div
        className="space-y-6"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {/* Header greeting */}
        <motion.div variants={fadeInUp} className="space-y-1">
          <h1 className="text-3xl font-bold text-text-primary">
            {greeting}, <span className="text-brand-teal">{user?.first_name || user?.full_name?.split(' ')[0] || user?.name?.split(' ')[0]}</span>
          </h1>
          <p className="text-text-secondary">
            Here's your health overview for today
          </p>
        </motion.div>

        {/* Quick stats cards */}
        <motion.div 
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
          variants={fadeInUp}
        >
          {/* Lifestyle Points */}
          <GlowCard className="relative overflow-hidden">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Lifestyle Points</p>
                <div className="flex items-baseline gap-1">
                  <AnimatedNumber value={lifestylePoints?.total || lifestylePoints?.total_points || 0} className="text-3xl font-bold text-brand-teal" />
                  <span className="text-text-muted text-sm">pts</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-teal/10 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-brand-teal" />
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <div className="flex-1 h-2 bg-bg-elevated rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-brand-teal rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(((lifestylePoints?.total || lifestylePoints?.total_points || 0) / 100) * 100, 100)}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
              </div>
              <span className="text-xs text-text-muted">/ 100</span>
            </div>
          </GlowCard>

          {/* Calories */}
          <GlowCard>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Calories</p>
                <div className="flex items-baseline gap-1">
                  <AnimatedNumber value={dashboard?.calories_consumed || 0} className="text-3xl font-bold text-text-primary" />
                  <span className="text-text-muted text-sm">/ {roundCalories(dashboard?.calorie_target || 2000)}</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <Flame className="w-5 h-5 text-orange-400" />
              </div>
            </div>
            <SparkLine
              data={(trends?.calories || []).map(p => p.value || p.total || 0)}
              color="#F97316"
              className="mt-3"
            />
          </GlowCard>

          {/* Water */}
          <GlowCard>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Water</p>
                <div className="flex items-baseline gap-1">
                  <AnimatedNumber value={dashboard?.water_ml || 0} className="text-3xl font-bold text-text-primary" />
                  <span className="text-text-muted text-sm">/ {dashboard?.water_target_ml || 2500} ml</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Droplets className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <SparkLine
              data={(trends?.water || []).map(p => p.value || p.total || 0)}
              color="#3B82F6"
              className="mt-3"
            />
          </GlowCard>

          {/* Weight */}
          <GlowCard>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-text-secondary mb-1">Weight</p>
                <div className="flex items-baseline gap-1">
                  <AnimatedNumber value={dashboard?.weight_kg || 0} decimals={1} className="text-3xl font-bold text-text-primary" />
                  <span className="text-text-muted text-sm">kg</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-sky-500/10 flex items-center justify-center">
                <Scale className="w-5 h-5 text-sky-500" />
              </div>
            </div>
            <SparkLine
              data={(trends?.weight || []).map(p => p.value || p.total || 0)}
              color="#A855F7"
              className="mt-3"
            />
          </GlowCard>
        </motion.div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left - Today's Activity */}
          <motion.div className="lg:col-span-2 space-y-6" variants={fadeInUp}>
            {/* Workout card */}
            <GlowCard>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-brand-teal/10 flex items-center justify-center">
                    <Dumbbell className="w-6 h-6 text-brand-teal" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-text-primary">Today's Workout</h3>
                    <p className="text-sm text-text-secondary">
                      {dashboard?.workout?.name || 'No workout scheduled'}
                    </p>
                  </div>
                </div>
                <Link
                  href="/workout"
                  className="flex items-center gap-1 text-brand-teal hover:text-brand-tealDim transition-colors"
                >
                  <span className="text-sm font-medium">View</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              
              {dashboard?.workout ? (
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 rounded-lg bg-bg-elevated">
                    <AnimatedNumber value={dashboard.workout.exercises_count || 0} className="text-2xl font-bold text-text-primary" />
                    <p className="text-xs text-text-muted mt-1">Exercises</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-bg-elevated">
                    <AnimatedNumber value={dashboard.workout.duration_minutes || 0} className="text-2xl font-bold text-text-primary" />
                    <p className="text-xs text-text-muted mt-1">Minutes</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-bg-elevated">
                    <AnimatedNumber value={dashboard.workout.calories_burn || 0} className="text-2xl font-bold text-text-primary" />
                    <p className="text-xs text-text-muted mt-1">Est. Calories</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-text-muted">
                  No workout scheduled for today
                </div>
              )}
            </GlowCard>

            {/* Diet card */}
            <GlowCard>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                    <Utensils className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-text-primary">Today's Nutrition</h3>
                    <p className="text-sm text-text-secondary">
                      {dashboard?.diet?.meals_logged || 0} of {dashboard?.diet?.meals_planned || 0} meals logged
                    </p>
                  </div>
                </div>
                <Link
                  href="/diet"
                  className="flex items-center gap-1 text-brand-teal hover:text-brand-tealDim transition-colors"
                >
                  <span className="text-sm font-medium">View</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>

              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Calories', value: roundCalories(dashboard?.calories_consumed || 0), target: roundCalories(dashboard?.calorie_target || 2000), color: 'text-orange-400' },
                  { label: 'Protein', value: dashboard?.diet?.protein_g || 0, target: dashboard?.diet?.protein_target || 120, color: 'text-red-400', unit: 'g' },
                  { label: 'Carbs', value: dashboard?.diet?.carbs_g || 0, target: dashboard?.diet?.carbs_target || 200, color: 'text-yellow-400', unit: 'g' },
                  { label: 'Fat', value: dashboard?.diet?.fat_g || 0, target: dashboard?.diet?.fat_target || 60, color: 'text-blue-400', unit: 'g' },
                ].map((macro) => (
                  <div key={macro.label} className="text-center">
                    <CircularProgress
                      value={macro.value}
                      max={macro.target}
                      size={80}
                      strokeWidth={6}
                      showValue={false}
                      color={macro.color.replace('text-', '#').replace('-400', '')}
                    />
                    <div className="mt-2">
                      <p className={cn('text-sm font-semibold', macro.color)}>
                        <AnimatedNumber value={macro.value} className={macro.color} />
                        {macro.unit && <span className="text-xs">{macro.unit}</span>}
                      </p>
                      <p className="text-xs text-text-muted">{macro.label}</p>
                    </div>
                  </div>
                ))}
              </div>
            </GlowCard>
          </motion.div>

          {/* Right - Health metrics */}
          <motion.div className="space-y-6" variants={fadeInUp}>
            {/* Health Risks */}
            <GlowCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <Heart className="w-5 h-5 text-risk-high" />
                  Health Risks
                </h3>
                <Link
                  href="/health"
                  className="text-sm text-brand-teal hover:text-brand-tealDim transition-colors"
                >
                  Details
                </Link>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">Diabetes Risk</span>
                  <RiskBadge level={diabetesRisk} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">CVD Risk</span>
                  <RiskBadge level={cvdRisk} />
                </div>
              </div>
            </GlowCard>

            {/* Stress Level */}
            <GlowCard>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <Brain className="w-5 h-5 text-sky-500" />
                  Stress Level
                </h3>
                <Link
                  href="/lifestyle"
                  className="text-sm text-brand-teal hover:text-brand-tealDim transition-colors"
                >
                  Check
                </Link>
              </div>
              <div className="flex items-center justify-center py-4">
                <CircularProgress
                  value={dashboard?.stress_level || 0}
                  max={10}
                  size={120}
                  color={dashboard?.stress_level && dashboard.stress_level > 7 ? '#EF4444' : dashboard?.stress_level && dashboard.stress_level > 4 ? '#F59E0B' : '#10B981'}
                  label={dashboard?.stress_level && dashboard.stress_level > 7 ? 'High' : dashboard?.stress_level && dashboard.stress_level > 4 ? 'Moderate' : 'Low'}
                />
              </div>
            </GlowCard>

            {/* Quick actions */}
            <GlowCard>
              <h3 className="font-semibold text-text-primary mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { href: '/logs', label: 'Log Meal', icon: <Utensils className="w-4 h-4" /> },
                  { href: '/logs?tab=water', label: 'Log Water', icon: <Droplets className="w-4 h-4" /> },
                  { href: '/progress', label: 'Log Weight', icon: <Scale className="w-4 h-4" /> },
                  { href: '/lifestyle', label: 'Stress Check', icon: <Brain className="w-4 h-4" /> },
                ].map((action) => (
                  <Link
                    key={action.href}
                    href={action.href}
                    className="flex items-center gap-2 p-3 rounded-lg bg-bg-elevated border border-bg-border hover:border-brand-teal/30 hover:bg-brand-teal/5 transition-all"
                  >
                    <div className="text-brand-teal">{action.icon}</div>
                    <span className="text-sm text-text-secondary">{action.label}</span>
                  </Link>
                ))}
              </div>
            </GlowCard>
          </motion.div>
        </div>

        {/* Weekly trends chart */}
        <motion.div variants={fadeInUp}>
          <GlowCard>
            <div className="flex items-center justify-between mb-6">
              <SectionHeading title="Weekly Trends" subtitle="Your progress over the past 7 days" className="mb-0" />
              <Link
                href="/progress"
                className="flex items-center gap-1 text-brand-teal hover:text-brand-tealDim transition-colors"
              >
                <span className="text-sm font-medium">View All</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            {trends?.lifestyle_points && trends.lifestyle_points.length > 0 ? (
              <LineChart
                data={trends.lifestyle_points.map((point, index) => ({
                  label: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index] || `Day ${index + 1}`,
                  value: point.value || point.total || 0,
                }))}
                height={250}
                showGrid
              />
            ) : (
              <div className="h-[250px] flex items-center justify-center text-text-muted">
                No trend data available yet
              </div>
            )}
          </GlowCard>
        </motion.div>
      </motion.div>
    </PageTransition>
  );
}
