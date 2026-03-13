'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ProgressBarProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  color?: 'teal' | 'red' | 'amber' | 'green';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const colorClasses = {
  teal: 'bg-brand-teal',
  red: 'bg-risk-high',
  amber: 'bg-risk-moderate',
  green: 'bg-risk-low',
};

const sizeClasses = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

export function ProgressBar({
  value,
  max = 100,
  showLabel = false,
  color = 'teal',
  size = 'md',
  className = '',
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between text-sm mb-1">
          <span className="text-text-secondary">Progress</span>
          <span className="text-text-primary font-medium">{percentage.toFixed(0)}%</span>
        </div>
      )}
      <div className={cn('w-full rounded-full bg-bg-elevated overflow-hidden', sizeClasses[size])}>
        <motion.div
          className={cn('h-full rounded-full', colorClasses[color])}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

export default ProgressBar;
