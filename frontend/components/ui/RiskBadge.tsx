'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

type RiskLevel = 'low' | 'moderate' | 'high';

interface RiskBadgeProps {
  level: RiskLevel;
  label?: string;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const levelConfig = {
  low: {
    bg: 'bg-risk-low/10',
    border: 'border-risk-low/30',
    text: 'text-risk-low',
    glow: 'shadow-[0_0_10px_rgba(16,185,129,0.2)]',
  },
  moderate: {
    bg: 'bg-risk-moderate/10',
    border: 'border-risk-moderate/30',
    text: 'text-risk-moderate',
    glow: 'shadow-[0_0_10px_rgba(245,158,11,0.2)]',
  },
  high: {
    bg: 'bg-risk-high/10',
    border: 'border-risk-high/30',
    text: 'text-risk-high',
    glow: 'shadow-[0_0_10px_rgba(239,68,68,0.2)]',
  },
};

const sizeConfig = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base',
};

const defaultLabels: Record<RiskLevel, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
};

export function RiskBadge({
  level,
  label,
  pulse = false,
  size = 'md',
  className = '',
}: RiskBadgeProps) {
  const config = levelConfig[level];
  const displayLabel = label || defaultLabels[level];
  const shouldPulse = pulse || level === 'high';

  return (
    <motion.span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        config.bg,
        config.border,
        config.text,
        config.glow,
        sizeConfig[size],
        shouldPulse && 'animate-pulse',
        className
      )}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <span
        className={cn(
          'w-1.5 h-1.5 rounded-full mr-1.5',
          level === 'low' && 'bg-risk-low',
          level === 'moderate' && 'bg-risk-moderate',
          level === 'high' && 'bg-risk-high'
        )}
      />
      {displayLabel}
    </motion.span>
  );
}

export default RiskBadge;
