'use client';

import { useEffect, useState } from 'react';
import { useMotionValue, useSpring, MotionValue } from 'framer-motion';

interface UseAnimatedNumberOptions {
  duration?: number;
  decimals?: number;
}

export function useAnimatedNumber(
  value: number,
  options: UseAnimatedNumberOptions = {}
): { displayValue: string; motionValue: MotionValue<number> } {
  const { duration = 1000, decimals = 1 } = options;
  const [displayValue, setDisplayValue] = useState('0');
  
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, {
    damping: 50,
    stiffness: 100,
    duration: duration / 1000,
  });

  useEffect(() => {
    motionValue.set(value);
  }, [value, motionValue]);

  useEffect(() => {
    const unsubscribe = springValue.on('change', (latest) => {
      setDisplayValue(latest.toFixed(decimals));
    });
    
    return () => unsubscribe();
  }, [springValue, decimals]);

  return { displayValue, motionValue: springValue };
}

export default useAnimatedNumber;
