'use client';

import { forwardRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FloatingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  icon?: React.ReactNode;
}

export const FloatingInput = forwardRef<HTMLInputElement, FloatingInputProps>(
  ({ label, error, icon, className = '', type, value, onFocus, onBlur, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const isPasswordType = type === 'password';
    const inputType = isPasswordType && showPassword ? 'text' : type;
    const hasValue = value !== undefined && value !== '';
    const isFloating = isFocused || hasValue;

    return (
      <div className={cn('w-full', className)}>
        <div className="relative">
          {icon && (
            <div className={cn(
              'absolute left-4 top-1/2 -translate-y-1/2 transition-colors',
              isFloating ? 'text-brand-teal' : 'text-text-muted'
            )}>
              {icon}
            </div>
          )}
          <input
            ref={ref}
            type={inputType}
            value={value}
            className={cn(
              'w-full px-4 pt-6 pb-2 bg-bg-elevated border border-bg-border rounded-xl',
              'text-text-primary placeholder-transparent',
              'focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/20',
              'transition-all duration-200 peer',
              icon && 'pl-12',
              isPasswordType && 'pr-12',
              error && 'border-risk-high focus:border-risk-high focus:ring-risk-high/20'
            )}
            placeholder={label}
            onFocus={(e) => {
              setIsFocused(true);
              onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              onBlur?.(e);
            }}
            {...props}
          />
          <motion.label
            className={cn(
              'absolute left-4 transition-all duration-200 pointer-events-none',
              icon && 'left-12'
            )}
            animate={{
              top: isFloating ? '0.5rem' : '50%',
              y: isFloating ? '0%' : '-50%',
              fontSize: isFloating ? '0.75rem' : '0.875rem',
              color: isFocused ? '#14B8A6' : '#64748B',
            }}
            transition={{ duration: 0.2 }}
          >
            {label}
          </motion.label>
          {isPasswordType && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors"
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          )}
        </div>
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="mt-1.5 text-sm text-risk-high"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

FloatingInput.displayName = 'FloatingInput';

export default FloatingInput;
