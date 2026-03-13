'use client';

import { useRef, useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { cn } from '@/lib/utils';

interface GaugeArcProps {
  value: number;
  min?: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  unit?: string;
  segments?: { threshold: number; color: string }[];
  className?: string;
}

const defaultSegments = [
  { threshold: 30, color: '#10B981' }, // Green - low
  { threshold: 70, color: '#F59E0B' }, // Amber - moderate
  { threshold: 100, color: '#EF4444' }, // Red - high
];

export function GaugeArc({
  value,
  min = 0,
  max = 100,
  size = 200,
  strokeWidth = 16,
  label,
  unit = '%',
  segments = defaultSegments,
  className = '',
}: GaugeArcProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const [displayValue, setDisplayValue] = useState(0);

  const normalizedValue = Math.min(Math.max(value, min), max);
  const percentage = ((normalizedValue - min) / (max - min)) * 100;
  
  // Arc calculations (180 degree semi-circle)
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * Math.PI; // Half circle
  const offset = circumference - (percentage / 100) * circumference;

  // Determine color based on segments
  const currentColor = segments.reduce((color, segment) => {
    if (percentage <= segment.threshold) return color;
    return segment.color;
  }, segments[0].color);

  useEffect(() => {
    if (isInView) {
      const duration = 1000;
      const steps = 60;
      const increment = normalizedValue / steps;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= normalizedValue) {
          setDisplayValue(normalizedValue);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.round(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [isInView, normalizedValue]);

  return (
    <div
      ref={ref}
      className={cn('relative inline-flex flex-col items-center', className)}
    >
      <svg
        width={size}
        height={size / 2 + 20}
        viewBox={`0 0 ${size} ${size / 2 + 20}`}
      >
        {/* Track */}
        <path
          d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
          fill="none"
          stroke="#1E293B"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Progress arc */}
        <motion.path
          d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
          fill="none"
          stroke={currentColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={isInView ? { strokeDashoffset: offset } : { strokeDashoffset: circumference }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{
            filter: `drop-shadow(0 0 8px ${currentColor}60)`,
          }}
        />

        {/* Segment tick marks */}
        {segments.map((segment, index) => {
          const angle = ((segment.threshold / 100) * 180 - 90) * (Math.PI / 180);
          const x = size / 2 + (radius - strokeWidth / 2 - 8) * Math.cos(angle);
          const y = size / 2 + (radius - strokeWidth / 2 - 8) * Math.sin(angle);
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r={2}
              fill="#64748B"
            />
          );
        })}
      </svg>

      {/* Center value display */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-center">
        <div className="flex items-baseline justify-center">
          <span className="text-3xl font-bold text-text-primary tabular-nums">
            {displayValue}
          </span>
          <span className="text-lg text-text-secondary ml-1">{unit}</span>
        </div>
        {label && (
          <span className="text-sm text-text-muted">{label}</span>
        )}
      </div>
    </div>
  );
}

export default GaugeArc;
