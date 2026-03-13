'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { useUIStore, Toast as ToastType } from '@/store';
import { cn } from '@/lib/utils';

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const colors = {
  success: {
    bg: 'bg-brand-teal/10',
    border: 'border-brand-teal/30',
    icon: 'text-brand-teal',
  },
  error: {
    bg: 'bg-risk-high/10',
    border: 'border-risk-high/30',
    icon: 'text-risk-high',
  },
  warning: {
    bg: 'bg-risk-moderate/10',
    border: 'border-risk-moderate/30',
    icon: 'text-risk-moderate',
  },
  info: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    icon: 'text-blue-400',
  },
};

function ToastItem({ toast }: { toast: ToastType }) {
  const { removeToast } = useUIStore();
  const Icon = icons[toast.type];
  const colorConfig = colors[toast.type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 100, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border backdrop-blur-xl min-w-[320px] max-w-[420px]',
        colorConfig.bg,
        colorConfig.border
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', colorConfig.icon)} />
      <p className="flex-1 text-sm text-text-primary">
        {typeof toast.message === 'string' ? toast.message : JSON.stringify(toast.message)}
      </p>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-text-muted hover:text-text-primary transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

export function ToastContainer() {
  const { toasts } = useUIStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
}

export default ToastContainer;
