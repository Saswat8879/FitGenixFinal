'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { authApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import { FloatingInput } from '@/components/forms';
import { Button } from '@/components/ui';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setTokens } = useAuthStore();
  const { addToast } = useUIStore();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    try {
      const response = await authApi.login(data.email, data.password);
      setTokens(response.access_token, response.refresh_token);
      
      // Get user info
      const user = await authApi.me();
      setUser(user);

      addToast({ type: 'success', message: 'Welcome back!' });

      // Check if user needs onboarding
      if (!user.onboarding_completed) {
        router.push('/onboarding');
      } else {
        router.push('/dashboard');
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      addToast({
        type: 'error',
        message: typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((e: any) => e.msg || String(e)).join(', ') : 'Invalid email or password',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Mobile logo */}
      <div className="lg:hidden flex items-center justify-center mb-8">
        <Link href="/" className="inline-flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center">
            <span className="text-white font-bold text-lg">F</span>
          </div>
          <span className="text-2xl font-bold text-text-primary">FitGenix</span>
        </Link>
      </div>

      {/* Header */}
      <div className="text-center lg:text-left">
        <h2 className="text-3xl font-bold text-text-primary mb-2">Welcome back</h2>
        <p className="text-text-secondary">
          Sign in to continue your fitness journey
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FloatingInput
          label="Email"
          type="email"
          icon={<Mail className="w-5 h-5" />}
          error={errors.email?.message}
          {...register('email')}
        />

        <FloatingInput
          label="Password"
          type="password"
          icon={<Lock className="w-5 h-5" />}
          error={errors.password?.message}
          {...register('password')}
        />

        <div className="flex justify-end">
          <Link
            href="/auth/forgot-password"
            className="text-sm text-brand-teal hover:text-brand-tealDim transition-colors"
          >
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          loading={isLoading}
          className="w-full"
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Sign in
        </Button>
      </form>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-bg-border" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-bg-base text-text-muted">or continue with</span>
        </div>
      </div>

      {/* OAuth buttons */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/google`}
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Google
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/fit/connect?provider=google_fit`}
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          Fitbit
        </Button>
      </div>

      {/* Register link */}
      <p className="text-center text-text-secondary">
        Don't have an account?{' '}
        <Link
          href="/auth/register"
          className="text-brand-teal hover:text-brand-tealDim font-medium transition-colors"
        >
          Sign up free
        </Link>
      </p>
    </div>
  );
}
