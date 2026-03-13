'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { cn } from '@/lib/utils';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: DataPoint[];
  dataKey?: string;
  color?: string;
  height?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  horizontal?: boolean;
  barRadius?: number;
  className?: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 shadow-lg">
        <p className="text-sm text-text-secondary">{label}</p>
        <p className="text-lg font-semibold text-brand-teal">
          {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

export function BarChart({
  data,
  dataKey = 'value',
  color = '#14B8A6',
  height = 200,
  showGrid = false,
  showTooltip = true,
  horizontal = false,
  barRadius = 4,
  className = '',
}: BarChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      className={cn('w-full', className)}
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart
          data={data}
          layout={horizontal ? 'vertical' : 'horizontal'}
          margin={{ top: 5, right: 5, left: horizontal ? 0 : -20, bottom: 0 }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
              vertical={!horizontal}
              horizontal={horizontal}
            />
          )}
          <XAxis
            type={horizontal ? 'number' : 'category'}
            dataKey={horizontal ? undefined : 'label'}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#64748B', fontSize: 12 }}
          />
          <YAxis
            type={horizontal ? 'category' : 'number'}
            dataKey={horizontal ? 'label' : undefined}
            axisLine={false}
            tickLine={false}
            tick={{ fill: '#64748B', fontSize: 12 }}
            width={horizontal ? 80 : 40}
          />
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          <Bar
            dataKey={dataKey}
            radius={[barRadius, barRadius, barRadius, barRadius]}
            animationDuration={1000}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || color} />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

export default BarChart;
