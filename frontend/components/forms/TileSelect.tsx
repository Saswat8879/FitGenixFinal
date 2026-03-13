'use client';

import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TileOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode | string;
}

interface TileSelectProps {
  options: readonly TileOption[] | TileOption[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
  columns?: 1 | 2 | 3 | 4;
  label?: string;
  error?: string;
  className?: string;
}

const columnClasses = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
};

export function TileSelect({
  options,
  value,
  onChange,
  multiple = false,
  columns = 2,
  label,
  error,
  className = '',
}: TileSelectProps) {
  const selectedValues = Array.isArray(value) ? value : [value];

  const handleSelect = (optionValue: string) => {
    if (multiple) {
      const currentValues = selectedValues;
      const newValues = currentValues.includes(optionValue)
        ? currentValues.filter((v) => v !== optionValue)
        : [...currentValues, optionValue];
      onChange(newValues);
    } else {
      onChange(optionValue);
    }
  };

  const isSelected = (optionValue: string) => selectedValues.includes(optionValue);

  return (
    <div className={cn('w-full', className)}>
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label}
        </label>
      )}
      <div className={cn('grid gap-3', columnClasses[columns])}>
        {options.map((option) => {
          const selected = isSelected(option.value);
          return (
            <motion.button
              key={option.value}
              type="button"
              onClick={() => handleSelect(option.value)}
              className={cn(
                'relative flex flex-col items-center justify-center p-4 rounded-xl border text-center transition-all',
                selected
                  ? 'bg-brand-teal/10 border-brand-teal/50'
                  : 'bg-bg-elevated border-bg-border hover:border-text-muted'
              )}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              animate={{
                boxShadow: selected
                  ? '0 0 20px rgba(20, 184, 166, 0.15)'
                  : '0 0 0px rgba(20, 184, 166, 0)',
              }}
            >
              {/* Selection indicator */}
              {selected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-2 right-2 w-5 h-5 rounded-full bg-brand-teal flex items-center justify-center"
                >
                  <Check className="w-3 h-3 text-white" />
                </motion.div>
              )}

              {/* Icon */}
              {option.icon && (
                <div className={cn(
                  'mb-2 transition-colors',
                  selected ? 'text-brand-teal' : 'text-text-muted'
                )}>
                  {option.icon}
                </div>
              )}

              {/* Label */}
              <span className={cn(
                'font-medium transition-colors',
                selected ? 'text-text-primary' : 'text-text-secondary'
              )}>
                {option.label}
              </span>

              {/* Description */}
              {option.description && (
                <span className="text-xs text-text-muted mt-1">
                  {option.description}
                </span>
              )}
            </motion.button>
          );
        })}
      </div>
      {error && (
        <p className="mt-2 text-sm text-risk-high">{error}</p>
      )}
    </div>
  );
}

export default TileSelect;
