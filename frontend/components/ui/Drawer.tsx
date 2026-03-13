'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  position?: 'right' | 'bottom';
  className?: string;
}

export function Drawer({
  isOpen,
  onClose,
  title,
  children,
  position = 'right',
  className = '',
}: DrawerProps) {
  const isRight = position === 'right';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-bg-base/80 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.div
            initial={isRight ? { x: '100%' } : { y: '100%' }}
            animate={isRight ? { x: 0 } : { y: 0 }}
            exit={isRight ? { x: '100%' } : { y: '100%' }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className={cn(
              'absolute bg-bg-card border-bg-border',
              isRight
                ? 'top-0 right-0 h-full w-full max-w-md border-l'
                : 'bottom-0 left-0 right-0 max-h-[80vh] rounded-t-2xl border-t',
              className
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-bg-border">
              {title && (
                <h3 className="text-lg font-semibold text-text-primary">
                  {title}
                </h3>
              )}
              <button
                onClick={onClose}
                className="p-1 text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-y-auto">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default Drawer;
