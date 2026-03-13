'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Activity,
  Link,
  Unlink,
  Zap,
  CheckCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { fitApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  Button,
} from '@/components/ui';
import { cn } from '@/lib/utils';

export default function FitPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();

  const { data: status, isLoading } = useQuery({
    queryKey: ['fit', 'status'],
    queryFn: () => fitApi.getStatus(),
  });

  const connectMutation = useMutation({
    mutationFn: () => fitApi.connect(),
    onSuccess: (data) => {
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        queryClient.invalidateQueries({ queryKey: ['fit'] });
        addToast({ type: 'success', message: 'Connected successfully!' });
      }
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to connect' });
    },
  });

  const syncMutation = useMutation({
    mutationFn: (days: number) => fitApi.sync(days),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fit'] });
      addToast({ type: 'success', message: 'Data synced successfully!' });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to sync data' });
    },
  });

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-48 skeleton rounded-xl" />
      </PageTransition>
    );
  }

  const isConnected = status?.connected;

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Google Fit Integration"
          subtitle="Connect your Google Fit account to sync activity data"
        />

        <GlowCard>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div 
                className="w-14 h-14 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: 'rgba(66, 133, 244, 0.2)' }}
              >
                <Activity className="w-6 h-6" style={{ color: '#4285F4' }} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-text-primary">Google Fit</h3>
                  {isConnected ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-risk-low/10 text-risk-low text-xs">
                      <CheckCircle className="w-3 h-3" />
                      Connected
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-bg-elevated text-text-muted text-xs">
                      <AlertCircle className="w-3 h-3" />
                      Not connected
                    </span>
                  )}
                </div>
                <p className="text-sm text-text-secondary">
                  Sync your activity, steps, and heart rate from Google Fit
                </p>
                {isConnected && status?.expires_at && (
                  <p className="text-xs text-text-muted mt-1">
                    Token expires: {new Date(status.expires_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {isConnected && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => syncMutation.mutate(1)}
                  loading={syncMutation.isPending}
                  icon={<RefreshCw className="w-4 h-4" />}
                >
                  Sync
                </Button>
              )}
              <Button
                variant={isConnected ? 'outline' : 'primary'}
                onClick={() => connectMutation.mutate()}
                loading={connectMutation.isPending}
                icon={isConnected ? <Unlink className="w-4 h-4" /> : <Link className="w-4 h-4" />}
              >
                {isConnected ? 'Reconnect' : 'Connect'}
              </Button>
            </div>
          </div>
        </GlowCard>

        {/* Sync options for connected users */}
        {isConnected && (
          <GlowCard>
            <SectionHeading title="Sync Options" className="mb-4" />
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => syncMutation.mutate(1)}
                loading={syncMutation.isPending}
              >
                Sync Last Day
              </Button>
              <Button
                variant="outline"
                onClick={() => syncMutation.mutate(3)}
                loading={syncMutation.isPending}
              >
                Sync Last 3 Days
              </Button>
              <Button
                variant="outline"
                onClick={() => syncMutation.mutate(7)}
                loading={syncMutation.isPending}
              >
                Sync Last 7 Days
              </Button>
            </div>
          </GlowCard>
        )}

        {/* Info card */}
        <GlowCard className="bg-brand-teal/5 border-brand-teal/20">
          <div className="flex items-start gap-4">
            <Zap className="w-6 h-6 text-brand-teal flex-shrink-0" />
            <div>
              <h4 className="font-medium text-text-primary mb-1">Why connect Google Fit?</h4>
              <p className="text-sm text-text-secondary">
                Connecting Google Fit allows FitGenix to automatically track your 
                activity, steps, and exercise data. This information helps us provide 
                more accurate workout recommendations and track your progress automatically.
              </p>
            </div>
          </div>
        </GlowCard>
      </div>
    </PageTransition>
  );
}
