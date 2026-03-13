'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TabsProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className = '' }: TabsProps) {
  return (
    <div className={cn('relative flex border-b border-bg-border', className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            'relative px-4 py-2 text-sm font-medium transition-colors',
            activeTab === tab.id
              ? 'text-brand-teal'
              : 'text-text-secondary hover:text-text-primary'
          )}
        >
          {tab.label}
          {activeTab === tab.id && (
            <motion.div
              layoutId="tab-indicator"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-teal"
              transition={{ duration: 0.3, ease: 'easeInOut' }}
            />
          )}
        </button>
      ))}
    </div>
  );
}

export default Tabs;
