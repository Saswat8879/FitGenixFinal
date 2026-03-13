import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          base: '#EAF6FF',
          surface: '#F7FCFF',
          card: '#FFFFFF',
          elevated: '#E8F5F2',
          border: '#C9DDEA',
        },
        brand: {
          teal: '#0EA5E9',
          tealDim: '#10B981',
          tealGlow: 'rgba(14,165,233,0.18)',
        },
        risk: {
          low: '#10B981',
          moderate: '#F59E0B',
          high: '#EF4444',
        },
        text: {
          primary: '#101828',
          secondary: '#334155',
          muted: '#64748B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'DM Serif Display', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-subtle': 'bounce-subtle 1s ease-in-out infinite',
      },
      keyframes: {
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'glow': {
          '0%': { boxShadow: '0 0 5px rgba(14,165,233,0.2), 0 0 20px rgba(16,185,129,0.08)' },
          '100%': { boxShadow: '0 0 10px rgba(14,165,233,0.35), 0 0 40px rgba(16,185,129,0.14)' },
        },
        'bounce-subtle': {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'shimmer-gradient': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow-teal': '0 0 20px rgba(14,165,233,0.24)',
        'glow-teal-lg': '0 0 40px rgba(16,185,129,0.25)',
        'inner-glow': 'inset 0 0 20px rgba(14,165,233,0.08)',
      },
    },
  },
  plugins: [],
};

export default config;
