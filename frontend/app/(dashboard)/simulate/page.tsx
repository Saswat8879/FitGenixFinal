'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Beaker,
  Play,
  AlertTriangle,
  Dumbbell,
  Utensils,
  Sun,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  RefreshCw,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { simulateApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  Button,
  Tabs,
} from '@/components/ui';
import { NumberStepper, TileSelect } from '@/components/forms';
import { cn } from '@/lib/utils';

const SIMULATION_TYPES = [
  { value: 'full_day', label: 'Full Day', icon: <Sun className="w-5 h-5" />, description: 'Simulate a complete day of activity' },
  { value: 'workout', label: 'Workout', icon: <Dumbbell className="w-5 h-5" />, description: 'Simulate workout completion' },
  { value: 'meal', label: 'Meal Log', icon: <Utensils className="w-5 h-5" />, description: 'Simulate meal logging' },
  { value: 'stress', label: 'Stress Spike', icon: <Activity className="w-5 h-5" />, description: 'Simulate a stress event' },
];

const WEIGHT_DIRECTIONS = [
  { value: 'loss', label: 'Weight Loss', icon: <TrendingDown className="w-5 h-5" /> },
  { value: 'gain', label: 'Weight Gain', icon: <TrendingUp className="w-5 h-5" /> },
  { value: 'plateau', label: 'Plateau', icon: <Minus className="w-5 h-5" /> },
] as const;

interface SimulationResult {
  success: boolean;
  message: string;
  details?: any;
}

export default function SimulatePage() {
  const { user } = useAuthStore();
  const { addToast } = useUIStore();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState('simulate');
  const [simulationType, setSimulationType] = useState('full_day');
  const [weightDirection, setWeightDirection] = useState<'loss' | 'gain' | 'plateau'>('loss');
  const [weightDays, setWeightDays] = useState(30);
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  // Check admin access
  if (!user?.is_admin) {
    return (
      <PageTransition className="flex items-center justify-center min-h-[60vh]">
        <GlowCard className="max-w-md text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">Admin Access Required</h2>
          <p className="text-text-secondary">
            This page is only accessible to administrators for testing purposes.
          </p>
        </GlowCard>
      </PageTransition>
    );
  }

  const runSimulation = async (type: string) => {
    switch (type) {
      case 'full_day':
        return simulateApi.fullDay();
      case 'workout':
        return simulateApi.workoutComplete();
      case 'meal':
        return simulateApi.mealLog();
      case 'stress':
        return simulateApi.stressSpike();
      default:
        throw new Error('Unknown simulation type');
    }
  };

  const simulateMutation = useMutation({
    mutationFn: (type: string) => runSimulation(type),
    onSuccess: (data) => {
      const message = `${data.simulation_type.replace(/_/g, ' ')} simulation completed`;
      setResults((prev) => [...prev, { success: true, message, details: data.data }]);
      queryClient.invalidateQueries();
      addToast({ type: 'success', message });
    },
    onError: (error: any) => {
      setResults((prev) => [...prev, { success: false, message: error.message || 'Simulation failed' }]);
      addToast({ type: 'error', message: 'Simulation failed' });
    },
  });

  const weightTrendMutation = useMutation({
    mutationFn: ({ direction, days }: { direction: 'loss' | 'gain' | 'plateau'; days: number }) =>
      simulateApi.weightTrend(direction, days),
    onSuccess: (data) => {
      const message = `Weight ${data.simulation_type.replace(/_/g, ' ')} simulation completed`;
      setResults((prev) => [...prev, { success: true, message, details: data.data }]);
      queryClient.invalidateQueries();
      addToast({ type: 'success', message });
    },
    onError: (error: any) => {
      setResults((prev) => [...prev, { success: false, message: error.message || 'Failed' }]);
      addToast({ type: 'error', message: 'Weight trend simulation failed' });
    },
  });

  const resetMutation = useMutation({
    mutationFn: () => simulateApi.reset(),
    onSuccess: (data) => {
      queryClient.invalidateQueries();
      setResults([]);
      addToast({ type: 'success', message: data.message || 'Test data reset!' });
    },
    onError: (error: any) => {
      addToast({ type: 'error', message: error.message || 'Reset failed' });
    },
  });

  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      await simulateMutation.mutateAsync(simulationType);
    } finally {
      setIsRunning(false);
    }
  };

  const handleWeightTrend = async () => {
    setIsRunning(true);
    try {
      await weightTrendMutation.mutateAsync({ direction: weightDirection, days: weightDays });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center">
            <Beaker className="w-6 h-6 text-sky-500" />
          </div>
          <SectionHeading
            title="Admin Simulation"
            subtitle="Generate test data and simulate user activity"
            className="mb-0"
          />
        </div>

        {/* Warning banner */}
        <GlowCard className="bg-yellow-500/5 border-yellow-500/30">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-text-primary">Development Only</p>
              <p className="text-sm text-text-secondary">
                This page generates fake data for testing purposes. Do not use in production environments.
              </p>
            </div>
          </div>
        </GlowCard>

        <Tabs
          tabs={[
            { id: 'simulate', label: 'Simulate' },
            { id: 'database', label: 'Database' },
            { id: 'logs', label: 'Logs' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {activeTab === 'simulate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Simulations */}
            <GlowCard>
              <SectionHeading title="Quick Simulations" className="mb-4" />
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-3">
                    Simulation Type
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {SIMULATION_TYPES.map((type) => (
                      <button
                        key={type.value}
                        onClick={() => setSimulationType(type.value)}
                        className={cn(
                          'flex flex-col items-start gap-2 p-4 rounded-xl border transition-all',
                          simulationType === type.value
                            ? 'bg-brand-teal/10 border-brand-teal text-brand-teal'
                            : 'bg-bg-elevated border-bg-border text-text-secondary hover:border-brand-teal/30'
                        )}
                      >
                        <div className="flex items-center gap-2">
                          {type.icon}
                          <span className="font-medium">{type.label}</span>
                        </div>
                        <span className="text-xs text-text-muted">{type.description}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <Button
                  className="w-full"
                  onClick={handleRunSimulation}
                  loading={isRunning && !weightTrendMutation.isPending}
                  icon={<Play className="w-4 h-4" />}
                >
                  Run Simulation
                </Button>
              </div>
            </GlowCard>

            {/* Weight Trend Simulation */}
            <GlowCard>
              <SectionHeading title="Weight Trend" className="mb-4" />
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-3">
                    Trend Direction
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {WEIGHT_DIRECTIONS.map((dir) => (
                      <button
                        key={dir.value}
                        onClick={() => setWeightDirection(dir.value)}
                        className={cn(
                          'flex flex-col items-center gap-2 p-4 rounded-xl border transition-all',
                          weightDirection === dir.value
                            ? 'bg-brand-teal/10 border-brand-teal text-brand-teal'
                            : 'bg-bg-elevated border-bg-border text-text-secondary hover:border-brand-teal/30'
                        )}
                      >
                        {dir.icon}
                        <span className="font-medium text-sm">{dir.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <NumberStepper
                  label="Number of Days"
                  value={weightDays}
                  onChange={setWeightDays}
                  min={7}
                  max={90}
                />

                <Button
                  className="w-full"
                  onClick={handleWeightTrend}
                  loading={weightTrendMutation.isPending}
                  icon={<TrendingUp className="w-4 h-4" />}
                >
                  Simulate Weight Trend
                </Button>
              </div>
            </GlowCard>

            {/* Results */}
            <GlowCard className="lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <SectionHeading title="Results" className="mb-0" />
                {results.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setResults([])}
                  >
                    Clear
                  </Button>
                )}
              </div>
              
              {results.length === 0 ? (
                <div className="text-center py-12 text-text-muted">
                  <Beaker className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Run a simulation to see results</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {results.map((result, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        'flex items-start gap-2 p-3 rounded-lg text-sm',
                        result.success ? 'bg-risk-low/10' : 'bg-risk-high/10'
                      )}
                    >
                      {result.success ? (
                        <CheckCircle className="w-4 h-4 text-risk-low flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-4 h-4 text-risk-high flex-shrink-0 mt-0.5" />
                      )}
                      <span className={result.success ? 'text-risk-low' : 'text-risk-high'}>
                        {result.message}
                      </span>
                    </motion.div>
                  ))}
                </div>
              )}
            </GlowCard>
          </div>
        )}

        {activeTab === 'database' && (
          <GlowCard>
            <div className="flex items-center gap-3 mb-4">
              <RefreshCw className="w-6 h-6 text-orange-400" />
              <div>
                <h3 className="font-semibold text-text-primary">Reset Test Data</h3>
                <p className="text-sm text-text-muted">Clear simulated data</p>
              </div>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Removes all data generated through simulations. This clears workout logs, meal logs, 
              health metrics, and simulated activity data. User accounts remain intact.
            </p>
            <Button
              variant="outline"
              onClick={() => resetMutation.mutate()}
              loading={resetMutation.isPending}
              className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
              icon={<RefreshCw className="w-4 h-4" />}
            >
              Reset Simulated Data
            </Button>
          </GlowCard>
        )}

        {activeTab === 'logs' && (
          <GlowCard>
            <SectionHeading title="Simulation Logs" className="mb-4" />
            <div className="bg-bg-base rounded-lg p-4 font-mono text-sm text-text-secondary max-h-96 overflow-y-auto">
              {results.length === 0 ? (
                <p className="text-text-muted">No simulation logs yet</p>
              ) : (
                results.map((result, i) => (
                  <div key={i} className="mb-2">
                    <span className={result.success ? 'text-risk-low' : 'text-risk-high'}>
                      [{result.success ? 'SUCCESS' : 'ERROR'}]
                    </span>{' '}
                    {result.message}
                    {result.details && (
                      <pre className="mt-1 text-xs text-text-muted pl-4">
                        {JSON.stringify(result.details, null, 2)}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </GlowCard>
        )}
      </div>
    </PageTransition>
  );
}
