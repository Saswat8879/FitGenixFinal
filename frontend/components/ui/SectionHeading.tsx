'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function SectionHeading({ title, subtitle, className = '' }: SectionHeadingProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <div ref={ref} className={cn('mb-6', className)}>
      <h2 className="text-2xl font-bold text-text-primary mb-1">{title}</h2>
      
      {/* Animated underline */}
      <motion.div
        className="h-0.5 bg-gradient-to-r from-brand-teal to-transparent"
        initial={{ width: 0 }}
        animate={isInView ? { width: '4rem' } : { width: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
      />
      
      {subtitle && (
        <motion.p
          className="text-text-secondary mt-2"
          initial={{ opacity: 0, y: 10 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          {subtitle}
        </motion.p>
      )}
    </div>
  );
}

export default SectionHeading;
