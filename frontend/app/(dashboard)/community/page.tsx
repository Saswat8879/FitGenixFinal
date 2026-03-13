'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Trophy,
  Medal,
  Crown,
  TrendingUp,
  Users,
  Flame,
  Star,
} from 'lucide-react';
import { communityApi } from '@/api';
import { useAuthStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Tabs,
} from '@/components/ui';
import { cn } from '@/lib/utils';

const MEDAL_COLORS = {
  1: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', icon: Crown },
  2: { bg: 'bg-gray-400/10', text: 'text-gray-300', icon: Medal },
  3: { bg: 'bg-amber-600/10', text: 'text-amber-500', icon: Medal },
};

export default function CommunityPage() {
  const { user } = useAuthStore();

  const { data: leaderboard, isLoading } = useQuery({
    queryKey: ['community', 'leaderboard'],
    queryFn: () => communityApi.getLeaderboard(),
  });

  // Use the same leaderboard for weekly view (same data, just displayed differently)
  const weeklyLeaderboard = leaderboard;

  const currentUserRank = leaderboard?.entries?.findIndex((u) => u.user_id === user?.id) !== -1 
    ? (leaderboard?.entries?.findIndex((u) => u.user_id === user?.id) ?? 0) + 1 
    : 0;

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-64 skeleton rounded-xl" />
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Community"
          subtitle="See how you stack up against other FitGenix members"
        />

        {/* Your rank card */}
        {currentUserRank > 0 && (
          <GlowCard className="bg-gradient-to-br from-brand-teal/10 to-brand-tealDim/10 border-brand-teal/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-brand-teal/20 flex items-center justify-center">
                  <Trophy className="w-8 h-8 text-brand-teal" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Your Current Rank</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-text-primary">#{currentUserRank}</span>
                    <span className="text-text-muted">of {leaderboard?.total || leaderboard?.entries?.length || 0}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-text-secondary">Your Points</p>
                <AnimatedNumber
                  value={leaderboard?.entries?.[currentUserRank - 1]?.total_points || 0}
                  className="text-3xl font-bold text-brand-teal"
                />
              </div>
            </div>
          </GlowCard>
        )}

        {/* Top 3 podium */}
        <div className="grid grid-cols-3 gap-4">
          {[1, 0, 2].map((position) => {
            const rank = position + 1;
            const entry = leaderboard?.entries?.[position];
            if (!entry) return <div key={position} />;

            const medalConfig = MEDAL_COLORS[rank as keyof typeof MEDAL_COLORS] || { bg: 'bg-bg-elevated', text: 'text-text-secondary', icon: Star };
            const MedalIcon = medalConfig.icon;

            return (
              <motion.div
                key={position}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: position * 0.1 }}
                className={cn(
                  'relative',
                  rank === 1 ? 'mt-0' : 'mt-8'
                )}
              >
                <GlowCard className={cn(
                  'text-center py-6',
                  rank === 1 && 'border-yellow-500/30'
                )}>
                  <div className={cn(
                    'w-12 h-12 rounded-full mx-auto mb-3 flex items-center justify-center',
                    medalConfig.bg
                  )}>
                    <MedalIcon className={cn('w-6 h-6', medalConfig.text)} />
                  </div>
                  <p className="text-xl font-bold text-text-primary mb-1">
                    #{rank}
                  </p>
                  <p className="text-sm text-text-secondary truncate px-2">
                    {entry.name || 'User'}
                  </p>
                  <div className="flex items-center justify-center gap-1 mt-2">
                    <Flame className="w-4 h-4 text-orange-400" />
                    <AnimatedNumber
                      value={entry.total_points}
                      className="font-semibold text-text-primary"
                    />
                  </div>
                </GlowCard>
              </motion.div>
            );
          })}
        </div>

        {/* Full leaderboard */}
        <GlowCard>
          <SectionHeading title="All-Time Leaderboard" className="mb-4" />
          <div className="space-y-2">
            {leaderboard?.entries?.slice(3).map((entry, i: number) => {
              const rank = i + 4;
              const isCurrentUser = entry.user_id === user?.id;
              
              return (
                <motion.div
                  key={entry.user_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className={cn(
                    'flex items-center gap-4 p-3 rounded-lg',
                    isCurrentUser ? 'bg-brand-teal/10 border border-brand-teal/30' : 'bg-bg-elevated'
                  )}
                >
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
                    isCurrentUser ? 'bg-brand-teal text-white' : 'bg-bg-border text-text-secondary'
                  )}>
                    {rank}
                  </div>
                  <div className="flex-1">
                    <p className={cn(
                      'font-medium',
                      isCurrentUser ? 'text-brand-teal' : 'text-text-primary'
                    )}>
                      {entry.name || 'User'}
                      {isCurrentUser && <span className="text-xs ml-2">(You)</span>}
                    </p>
                    <p className="text-xs text-text-muted">
                      {entry.streak || 0} day streak
                    </p>
                  </div>
                  <div className="text-right">
                    <AnimatedNumber
                      value={entry.total_points}
                      className="font-semibold text-text-primary"
                    />
                    <p className="text-xs text-text-muted">pts</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </GlowCard>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <GlowCard>
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-sky-500" />
              <div>
                <p className="text-sm text-text-secondary">Total Members</p>
                <AnimatedNumber
                  value={leaderboard?.total || leaderboard?.entries?.length || 0}
                  className="text-2xl font-bold text-text-primary"
                />
              </div>
            </div>
          </GlowCard>
          <GlowCard>
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-brand-teal" />
              <div>
                <p className="text-sm text-text-secondary">Avg Points</p>
                <AnimatedNumber
                  value={leaderboard?.entries?.reduce((sum: number, u) => sum + u.total_points, 0)! / (leaderboard?.entries?.length || 1) || 0}
                  className="text-2xl font-bold text-text-primary"
                />
              </div>
            </div>
          </GlowCard>
        </div>
      </div>
    </PageTransition>
  );
}
