'use client';

import { forwardRef, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  options: SelectOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  className?: string;
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(
  ({ options, value, onChange, placeholder = 'Select...', label, error, className = '' }, ref) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const selectedOption = options.find((opt) => opt.value === value);

    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
          setIsOpen(false);
        }
      };

      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
      <div ref={ref} className={cn('w-full', className)}>
        {label && (
          <label className="block text-sm font-medium text-text-secondary mb-1.5">
            {label}
          </label>
        )}
        <div ref={containerRef} className="relative">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className={cn(
              'w-full flex items-center justify-between px-4 py-2.5',
              'bg-bg-elevated border border-bg-border rounded-lg',
              'text-left transition-all duration-200',
              'focus:outline-none focus:border-brand-teal focus:ring-2 focus:ring-brand-teal/20',
              error && 'border-risk-high',
              isOpen && 'border-brand-teal'
            )}
          >
            <span className={selectedOption ? 'text-text-primary' : 'text-text-muted'}>
              {selectedOption?.label || placeholder}
            </span>
            <ChevronDown
              className={cn(
                'w-4 h-4 text-text-muted transition-transform',
                isOpen && 'rotate-180'
              )}
            />
          </button>

          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.15 }}
                className={cn(
                  'absolute z-50 w-full mt-1 py-1',
                  'bg-bg-elevated border border-bg-border rounded-lg shadow-xl',
                  'max-h-60 overflow-y-auto'
                )}
              >
                {options.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onChange(option.value);
                      setIsOpen(false);
                    }}
                    className={cn(
                      'w-full flex items-center justify-between px-4 py-2',
                      'text-left text-sm transition-colors',
                      option.value === value
                        ? 'bg-brand-teal/10 text-brand-teal'
                        : 'text-text-primary hover:bg-bg-border'
                    )}
                  >
                    {option.label}
                    {option.value === value && <Check className="w-4 h-4" />}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        {error && (
          <p className="mt-1.5 text-sm text-risk-high">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export default Select;
