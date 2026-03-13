'use client';

import { cn } from '@/lib/utils';

interface SkeletonLoaderProps {
  className?: string;
  variant?: 'line' | 'circle' | 'card';
  lines?: number;
}

export function SkeletonLoader({
  className = '',
  variant = 'line',
  lines = 1,
}: SkeletonLoaderProps) {
  if (variant === 'circle') {
    return (
      <div
        className={cn(
          'rounded-full skeleton',
          className
        )}
      />
    );
  }

  if (variant === 'card') {
    return (
      <div className={cn('rounded-xl overflow-hidden', className)}>
        <div className="skeleton h-32 w-full" />
        <div className="p-4 space-y-3">
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-4 w-1/2 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'skeleton h-4 rounded',
            i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  );
}

export default SkeletonLoader;
