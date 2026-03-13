'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type MotionButtonProps = HTMLMotionProps<'button'>;

interface ButtonProps extends Omit<MotionButtonProps, 'children'> {
  children?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

const variantStyles = {
  primary: 'bg-gradient-to-r from-brand-teal to-brand-tealDim text-white hover:shadow-glow-teal btn-shimmer',
  secondary: 'bg-bg-elevated text-text-primary hover:bg-bg-border',
  outline: 'border border-bg-border text-text-primary hover:border-brand-teal hover:text-brand-teal',
  ghost: 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated',
  danger: 'bg-risk-high/10 text-risk-high border border-risk-high/30 hover:bg-risk-high/20',
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <motion.button
      whileHover={!isDisabled ? { scale: 1.02 } : undefined}
      whileTap={!isDisabled ? { scale: 0.98 } : undefined}
      className={cn(
        'relative inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-brand-teal/50 focus:ring-offset-2 focus:ring-offset-bg-surface',
        variantStyles[variant],
        sizeStyles[size],
        isDisabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <Loader2 className="w-4 h-4 animate-spin" />
      )}
      {!loading && icon && iconPosition === 'left' && icon}
      {children}
      {!loading && icon && iconPosition === 'right' && icon}
    </motion.button>
  );
}

export default Button;
