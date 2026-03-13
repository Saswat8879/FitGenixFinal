'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function Toggle({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}: ToggleProps) {
  return (
    <label
      className={cn(
        'flex items-start gap-3 cursor-pointer',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 flex-shrink-0 rounded-full transition-colors duration-200',
          checked ? 'bg-brand-teal' : 'bg-bg-border'
        )}
      >
        <motion.span
          className="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm"
          animate={{
            x: checked ? 22 : 2,
          }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
          style={{ marginTop: 2 }}
        />
      </button>
      {(label || description) && (
        <div className="flex-1">
          {label && (
            <span className="text-sm font-medium text-text-primary">{label}</span>
          )}
          {description && (
            <p className="text-sm text-text-muted">{description}</p>
          )}
        </div>
      )}
    </label>
  );
}

export default Toggle;
