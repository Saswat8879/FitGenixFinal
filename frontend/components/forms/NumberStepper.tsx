'use client';

import { motion } from 'framer-motion';
import { Minus, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NumberStepperProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  unit?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: {
    container: 'h-8',
    button: 'w-8 h-8',
    icon: 'w-3 h-3',
    value: 'w-12 text-sm',
  },
  md: {
    container: 'h-10',
    button: 'w-10 h-10',
    icon: 'w-4 h-4',
    value: 'w-16 text-base',
  },
  lg: {
    container: 'h-12',
    button: 'w-12 h-12',
    icon: 'w-5 h-5',
    value: 'w-20 text-lg',
  },
};

export function NumberStepper({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  label,
  unit,
  size = 'md',
  className = '',
}: NumberStepperProps) {
  const styles = sizeClasses[size];

  const handleDecrement = () => {
    const newValue = Math.max(value - step, min);
    onChange(newValue);
  };

  const handleIncrement = () => {
    const newValue = Math.min(value + step, max);
    onChange(newValue);
  };

  const canDecrement = value > min;
  const canIncrement = value < max;

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {label && (
        <label className="text-sm font-medium text-text-secondary">{label}</label>
      )}
      <div className={cn('inline-flex items-center rounded-lg border border-bg-border bg-bg-elevated overflow-hidden', styles.container)}>
        <motion.button
          type="button"
          onClick={handleDecrement}
          disabled={!canDecrement}
          className={cn(
            'flex items-center justify-center border-r border-bg-border',
            'text-text-secondary hover:text-text-primary hover:bg-bg-border',
            'transition-colors disabled:opacity-30 disabled:cursor-not-allowed',
            styles.button
          )}
          whileTap={canDecrement ? { scale: 0.9 } : undefined}
        >
          <Minus className={styles.icon} />
        </motion.button>
        
        <div className={cn('flex items-center justify-center font-medium text-text-primary', styles.value)}>
          {value}
          {unit && <span className="text-text-muted ml-0.5">{unit}</span>}
        </div>
        
        <motion.button
          type="button"
          onClick={handleIncrement}
          disabled={!canIncrement}
          className={cn(
            'flex items-center justify-center border-l border-bg-border',
            'text-text-secondary hover:text-text-primary hover:bg-bg-border',
            'transition-colors disabled:opacity-30 disabled:cursor-not-allowed',
            styles.button
          )}
          whileTap={canIncrement ? { scale: 0.9 } : undefined}
        >
          <Plus className={styles.icon} />
        </motion.button>
      </div>
    </div>
  );
}

export default NumberStepper;
