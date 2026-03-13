'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GlowCardProps {
  children: ReactNode;
  className?: string;
  glowOnHover?: boolean;
  onClick?: () => void;
}

export function GlowCard({
  children,
  className = '',
  glowOnHover = true,
  onClick,
}: GlowCardProps) {
  return (
    <motion.div
      className={cn(
        'relative rounded-xl bg-white/70 backdrop-blur-xl border border-white/70 p-6 overflow-hidden shadow-[0_12px_35px_rgba(15,23,42,0.08)]',
        'transition-all duration-300',
        onClick && 'cursor-pointer',
        className
      )}
      whileHover={glowOnHover ? {
        borderColor: 'rgba(14, 165, 233, 0.35)',
        boxShadow: '0 0 30px rgba(14, 165, 233, 0.14), 0 0 60px rgba(16, 185, 129, 0.07)',
      } : undefined}
      transition={{ duration: 0.3 }}
      onClick={onClick}
    >
      {/* Gradient border effect on hover */}
      <motion.div
        className="absolute inset-0 rounded-xl pointer-events-none"
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        style={{
          background: 'radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(14, 165, 233, 0.08), transparent 42%)',
        }}
      />
      
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

export default GlowCard;
