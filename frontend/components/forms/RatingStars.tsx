'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RatingStarsProps {
  value: number;
  onChange?: (value: number) => void;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  readOnly?: boolean;
  showValue?: boolean;
  label?: string;
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export function RatingStars({
  value,
  onChange,
  max = 5,
  size = 'md',
  readOnly = false,
  showValue = false,
  label,
  className = '',
}: RatingStarsProps) {
  const [hoverValue, setHoverValue] = useState(0);
  const displayValue = hoverValue || value;

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {label && (
        <label className="text-sm font-medium text-text-secondary">{label}</label>
      )}
      <div className="flex items-center gap-1">
        {Array.from({ length: max }).map((_, index) => {
          const starValue = index + 1;
          const isFilled = displayValue >= starValue;
          
          return (
            <motion.button
              key={index}
              type="button"
              disabled={readOnly}
              onClick={() => onChange?.(starValue)}
              onMouseEnter={() => !readOnly && setHoverValue(starValue)}
              onMouseLeave={() => setHoverValue(0)}
              className={cn(
                'relative transition-colors',
                !readOnly && 'cursor-pointer hover:scale-110'
              )}
              whileHover={!readOnly ? { scale: 1.15 } : undefined}
              whileTap={!readOnly ? { scale: 0.95 } : undefined}
            >
              <Star
                className={cn(
                  sizeClasses[size],
                  'transition-all duration-200',
                  isFilled
                    ? 'text-yellow-400 fill-yellow-400 drop-shadow-[0_0_4px_rgba(250,204,21,0.5)]'
                    : 'text-text-muted'
                )}
              />
            </motion.button>
          );
        })}
        {showValue && (
          <span className="ml-2 text-sm text-text-secondary">
            {value}/{max}
          </span>
        )}
      </div>
    </div>
  );
}

export default RatingStars;
