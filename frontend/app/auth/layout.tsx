'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative isolate min-h-screen overflow-hidden">
      <video
        className="absolute inset-0 z-0 h-full w-full object-cover opacity-18 pointer-events-none"
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        aria-hidden="true"
      >
        <source src="/assets/background_auth.mp4?v=20260313" type="video/mp4" />
      </video>
      <div className="absolute inset-0 z-10 bg-gradient-to-br from-white/88 via-blue-50/84 to-emerald-50/86" />

      <div className="relative z-20 min-h-screen flex">
        {/* Left side - Branding */}
        <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden border-r border-white/55 bg-white/28">
          <motion.div
            className="absolute w-96 h-96 rounded-full bg-brand-teal/20 blur-3xl"
            animate={{
              x: [0, 50, 0],
              y: [0, -30, 0],
            }}
            transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
            style={{ top: '20%', left: '10%' }}
          />
          <motion.div
            className="absolute w-64 h-64 rounded-full bg-brand-tealDim/20 blur-3xl"
            animate={{
              x: [0, -30, 0],
              y: [0, 40, 0],
            }}
            transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
            style={{ bottom: '30%', right: '20%' }}
          />

          <div className="relative z-10 flex flex-col justify-center p-12">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Link href="/" className="inline-flex items-center gap-3 mb-12">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-2xl">F</span>
                </div>
                <span className="text-3xl font-bold text-text-primary">FitGenix</span>
              </Link>

              <h1 className="text-5xl font-serif text-text-primary mb-6 leading-tight">
                Transform your health with{' '}
                <span className="text-brand-teal">AI-powered</span> precision
              </h1>
              <p className="text-xl text-text-secondary max-w-md">
                Personalized workout plans, nutrition guidance, and lifestyle optimization
                tailored uniquely to you.
              </p>
            </motion.div>

            <motion.div
              className="flex flex-wrap gap-3 mt-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {['Smart Workouts', 'Nutrition AI', 'Stress Detection', 'Health Tracking'].map((feature) => (
                <span
                  key={feature}
                  className="px-4 py-2 rounded-full bg-white/65 border border-white/70 text-text-secondary text-sm backdrop-blur"
                >
                  {feature}
                </span>
              ))}
            </motion.div>
          </div>
        </div>

        {/* Right side - Auth form */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-white/22">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
            className="w-full max-w-md rounded-3xl glass p-6 sm:p-8"
          >
            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
