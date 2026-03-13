'use client';

import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToggleChipProps {
  label: string;
  selected: boolean;
  onChange: (selected: boolean) => void;
  icon?: React.ReactNode;
  disabled?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
};

export function ToggleChip({
  label,
  selected,
  onChange,
  icon,
  disabled = false,
  size = 'md',
  className = '',
}: ToggleChipProps) {
  return (
    <motion.button
      type="button"
      disabled={disabled}
      onClick={() => onChange(!selected)}
      className={cn(
        'inline-flex items-center gap-2 rounded-full border font-medium transition-all',
        sizeClasses[size],
        selected
          ? 'bg-brand-teal/10 border-brand-teal/50 text-brand-teal'
          : 'bg-bg-elevated border-bg-border text-text-secondary hover:border-text-muted',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      whileHover={!disabled ? { scale: 1.02 } : undefined}
      whileTap={!disabled ? { scale: 0.98 } : undefined}
      animate={{
        boxShadow: selected
          ? '0 0 12px rgba(20, 184, 166, 0.2)'
          : '0 0 0px rgba(20, 184, 166, 0)',
      }}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{label}</span>
      {selected && (
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0 }}
          transition={{ duration: 0.2 }}
        >
          <Check className="w-3.5 h-3.5" />
        </motion.span>
      )}
    </motion.button>
  );
}

export default ToggleChip;
