'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Heart,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Info,
} from 'lucide-react';
import { healthApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  RiskBadge,
} from '@/components/ui';
import { GaugeArc } from '@/components/charts';
import { cn, getRiskLevel } from '@/lib/utils';

export default function HealthPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();

  // Fetch health metrics (includes current risk scores)
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['health', 'metrics'],
    queryFn: () => healthApi.getMetrics(),
  });

  // Mutations for running risk assessments
  const diabetesMutation = useMutation({
    mutationFn: () => healthApi.runDiabetesRisk(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['health'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addToast({ type: 'info', message: `Diabetes risk: ${data.category}` });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to compute diabetes risk' });
    },
  });

  const cvdMutation = useMutation({
    mutationFn: () => healthApi.runCvdRisk(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['health'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addToast({ type: 'info', message: `CVD risk: ${data.category}` });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to compute CVD risk' });
    },
  });

  const refreshMutation = useMutation({
    mutationFn: () => healthApi.refreshAllRisks(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      addToast({ type: 'success', message: 'All risks refreshed' });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to refresh risks' });
    },
  });

  const diabetesRisk = metrics?.diabetes_risk_score || 0;
  const cvdRisk = metrics?.cvd_risk_score || 0;

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 skeleton rounded-xl" />
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
            title="Health Assessment"
            subtitle="Monitor your health risks and get personalized recommendations"
          />
          <Button
            variant="outline"
            onClick={() => refreshMutation.mutate()}
            loading={refreshMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh All
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Diabetes risk */}
          <GlowCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-sky-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">Diabetes Risk</h3>
                  <RiskBadge level={getRiskLevel(diabetesRisk)} />
                </div>
              </div>
            </div>
            
            <div className="flex justify-center my-6">
              <GaugeArc
                value={diabetesRisk * 100}
                size={160}
                label={`${(diabetesRisk * 100).toFixed(0)}%`}
              />
            </div>

            {metrics?.diabetes_risk_category && (
              <p className="text-center text-sm text-text-secondary mb-4">
                Category: {metrics.diabetes_risk_category}
              </p>
            )}

            <Button
              variant="outline"
              className="w-full"
              onClick={() => diabetesMutation.mutate()}
              loading={diabetesMutation.isPending}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              Run Assessment
            </Button>
          </GlowCard>

          {/* CVD risk */}
          <GlowCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-red-500/10 flex items-center justify-center">
                  <Heart className="w-6 h-6 text-red-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">Cardiovascular Risk</h3>
                  <RiskBadge level={getRiskLevel(cvdRisk)} />
                </div>
              </div>
            </div>
            
            <div className="flex justify-center my-6">
              <GaugeArc
                value={cvdRisk * 100}
                size={160}
                label={`${(cvdRisk * 100).toFixed(0)}%`}
              />
            </div>

            <p className="text-center text-sm text-text-secondary mb-4">
              Based on age, BMI, and lifestyle factors
            </p>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => cvdMutation.mutate()}
              loading={cvdMutation.isPending}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              Run Assessment
            </Button>
          </GlowCard>
        </div>

        {/* Health Metrics */}
        <GlowCard>
          <SectionHeading 
            title="Health Metrics" 
            subtitle="Your current health data"
            className="mb-4"
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-bg-elevated">
              <p className="text-sm text-text-muted">BMI</p>
              <p className="text-2xl font-bold text-text-primary">
                {metrics?.bmi?.toFixed(1) || '--'}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated">
              <p className="text-sm text-text-muted">Weight</p>
              <p className="text-2xl font-bold text-text-primary">
                {metrics?.weight_kg ? `${metrics.weight_kg} kg` : '--'}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated">
              <p className="text-sm text-text-muted">Resting HR</p>
              <p className="text-2xl font-bold text-text-primary">
                {metrics?.resting_hr ? `${metrics.resting_hr} bpm` : '--'}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated">
              <p className="text-sm text-text-muted">Stress Level</p>
              <p className="text-2xl font-bold text-text-primary">
                {metrics?.stress_level ?? '--'}
              </p>
            </div>
          </div>
        </GlowCard>

        {/* Activity Summary */}
        <GlowCard>
          <SectionHeading 
            title="Activity Summary" 
            subtitle="Average daily metrics"
            className="mb-4"
          />
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-bg-elevated text-center">
              <p className="text-sm text-text-muted mb-1">Daily Steps</p>
              <AnimatedNumber
                value={metrics?.avg_daily_steps || 0}
                className="text-2xl font-bold text-text-primary"
              />
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated text-center">
              <p className="text-sm text-text-muted mb-1">Active Minutes</p>
              <AnimatedNumber
                value={metrics?.avg_active_minutes || 0}
                className="text-2xl font-bold text-text-primary"
              />
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated text-center">
              <p className="text-sm text-text-muted mb-1">Sleep Hours</p>
              <AnimatedNumber
                value={metrics?.avg_sleep_hours || 0}
                decimals={1}
                className="text-2xl font-bold text-text-primary"
              />
            </div>
          </div>
        </GlowCard>

        {/* Info card */}
        <GlowCard className="bg-yellow-500/10 border-yellow-500/30">
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-6 h-6 text-yellow-400 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-text-primary mb-1">Medical Disclaimer</h4>
              <p className="text-sm text-text-secondary">
                These assessments provide estimates based on general risk factors and your profile data. 
                They are not medical diagnoses. Please consult a healthcare professional for accurate 
                medical evaluation and advice.
              </p>
            </div>
          </div>
        </GlowCard>
      </div>
    </PageTransition>
  );
}
