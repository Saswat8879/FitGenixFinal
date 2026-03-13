'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
  AreaChart,
} from 'recharts';
import { cn } from '@/lib/utils';

interface DataPoint {
  label: string;
  value: number;
  [key: string]: any;
}

interface LineChartProps {
  data: DataPoint[];
  dataKey?: string;
  color?: string;
  height?: number;
  showGrid?: boolean;
  showArea?: boolean;
  gradientFill?: boolean;
  showDots?: boolean;
  showTooltip?: boolean;
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

export function LineChart({
  data,
  dataKey = 'value',
  color = '#14B8A6',
  height = 200,
  showGrid = false,
  showArea = true,
  gradientFill = true,
  showDots = true,
  showTooltip = true,
  className = '',
}: LineChartProps) {
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
        {showArea ? (
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
                vertical={false}
              />
            )}
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12 }}
              dx={-10}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              fill={gradientFill ? `url(#gradient-${color.replace('#', '')})` : 'transparent'}
              dot={showDots ? { fill: color, strokeWidth: 0, r: 3 } : false}
              activeDot={{ fill: color, strokeWidth: 2, stroke: '#fff', r: 5 }}
              animationDuration={1500}
              animationEasing="ease-out"
            />
          </AreaChart>
        ) : (
          <RechartsLineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            {showGrid && (
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
                vertical={false}
              />
            )}
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12 }}
              dx={-10}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={showDots ? { fill: color, strokeWidth: 0, r: 3 } : false}
              activeDot={{ fill: color, strokeWidth: 2, stroke: '#fff', r: 5 }}
              animationDuration={1500}
              animationEasing="ease-out"
            />
          </RechartsLineChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  );
}

export default LineChart;
