'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { cn } from '@/lib/utils';

interface DataSegment {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DataSegment[];
  size?: number;
  innerRadius?: number;
  outerRadius?: number;
  showTooltip?: boolean;
  centerLabel?: string;
  centerValue?: string | number;
  className?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 shadow-lg">
        <p className="text-sm text-text-secondary">{payload[0].name}</p>
        <p className="text-lg font-semibold" style={{ color: payload[0].payload.color }}>
          {payload[0].value}
        </p>
      </div>
    );
  }
  return null;
};

export function DonutChart({
  data,
  size = 200,
  innerRadius = 60,
  outerRadius = 80,
  showTooltip = true,
  centerLabel,
  centerValue,
  className = '',
}: DonutChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <motion.div
      ref={ref}
      className={cn('relative', className)}
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      <ResponsiveContainer width={size} height={size}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            nameKey="label"
            animationDuration={1000}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                style={{
                  filter: `drop-shadow(0 0 4px ${entry.color}40)`,
                }}
              />
            ))}
          </Pie>
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
        </PieChart>
      </ResponsiveContainer>

      {/* Center content */}
      {(centerLabel || centerValue) && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {centerValue && (
            <span className="text-2xl font-bold text-text-primary">{centerValue}</span>
          )}
          {centerLabel && (
            <span className="text-xs text-text-secondary">{centerLabel}</span>
          )}
        </div>
      )}
    </motion.div>
  );
}

export default DonutChart;
