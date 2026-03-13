'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
  marks?: { value: number; label: string }[];
  className?: string;
}

export function Slider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  label,
  showValue = true,
  formatValue = (v) => String(v),
  marks,
  className = '',
}: SliderProps) {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <label className="text-sm font-medium text-text-secondary">{label}</label>
          )}
          {showValue && (
            <span className="text-sm font-medium text-brand-teal tabular-nums">
              {formatValue(value)}
            </span>
          )}
        </div>
      )}
      
      <div className="relative h-6">
        {/* Track */}
        <div className="absolute top-1/2 -translate-y-1/2 w-full h-2 bg-bg-elevated rounded-full">
          {/* Fill */}
          <motion.div
            className="absolute h-full bg-brand-teal rounded-full"
            style={{ width: `${percentage}%` }}
            initial={false}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>

        {/* Input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className={cn(
            'absolute top-0 w-full h-6 opacity-0 cursor-pointer',
            '[&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:appearance-none'
          )}
        />

        {/* Thumb */}
        <motion.div
          className="absolute top-1/2 w-5 h-5 -translate-y-1/2 -translate-x-1/2 pointer-events-none"
          style={{ left: `${percentage}%` }}
          initial={false}
          animate={{ left: `${percentage}%` }}
          transition={{ duration: 0.1 }}
        >
          <div className="w-full h-full bg-white rounded-full shadow-lg border-2 border-brand-teal" />
        </motion.div>
      </div>

      {/* Marks */}
      {marks && marks.length > 0 && (
        <div className="relative mt-2">
          {marks.map((mark) => {
            const markPercentage = ((mark.value - min) / (max - min)) * 100;
            return (
              <div
                key={mark.value}
                className="absolute -translate-x-1/2"
                style={{ left: `${markPercentage}%` }}
              >
                <span className="text-xs text-text-muted">{mark.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Slider;
