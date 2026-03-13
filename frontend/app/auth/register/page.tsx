'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Check } from 'lucide-react';
import { authApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import { FloatingInput } from '@/components/forms';
import { Button } from '@/components/ui';

const registerSchema = z.object({
  firstName: z.string().min(2, 'First name must be at least 2 characters'),
  lastName: z.string().min(2, 'Last name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterForm = z.infer<typeof registerSchema>;

const passwordRequirements = [
  { label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
  { label: 'One uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'One lowercase letter', test: (p: string) => /[a-z]/.test(p) },
  { label: 'One number', test: (p: string) => /[0-9]/.test(p) },
];

export default function RegisterPage() {
  const router = useRouter();
  const { setUser, setTokens } = useAuthStore();
  const { addToast } = useUIStore();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const password = watch('password', '');

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true);
    try {
      await authApi.register({
        email: data.email,
        password: data.password,
        name: `${data.firstName} ${data.lastName}`.trim(),
        first_name: data.firstName,
        last_name: data.lastName,
      });

      // Auto-login after registration
      const loginResponse = await authApi.login(data.email, data.password);
      setTokens(loginResponse.access_token, loginResponse.refresh_token);

      const user = await authApi.me();
      setUser(user);

      addToast({ type: 'success', message: 'Account created successfully!' });
      router.push('/onboarding');
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      addToast({
        type: 'error',
        message: typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((e: any) => e.msg || String(e)).join(', ') : 'Failed to create account',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Mobile logo */}
      <div className="lg:hidden flex items-center justify-center mb-6">
        <Link href="/" className="inline-flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center">
            <span className="text-white font-bold text-lg">F</span>
          </div>
          <span className="text-2xl font-bold text-text-primary">FitGenix</span>
        </Link>
      </div>

      {/* Header */}
      <div className="text-center lg:text-left">
        <h2 className="text-3xl font-bold text-text-primary mb-2">Create account</h2>
        <p className="text-text-secondary">
          Start your personalized fitness journey today
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <FloatingInput
            label="First name"
            icon={<User className="w-5 h-5" />}
            error={errors.firstName?.message}
            {...register('firstName')}
          />
          <FloatingInput
            label="Last name"
            error={errors.lastName?.message}
            {...register('lastName')}
          />
        </div>

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

        {/* Password requirements */}
        {password && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="space-y-1"
          >
            {passwordRequirements.map((req) => {
              const passed = req.test(password);
              return (
                <div
                  key={req.label}
                  className="flex items-center gap-2 text-xs"
                >
                  <div
                    className={`w-4 h-4 rounded-full flex items-center justify-center ${
                      passed
                        ? 'bg-risk-low text-white'
                        : 'bg-bg-border text-text-muted'
                    }`}
                  >
                    <Check className="w-2.5 h-2.5" />
                  </div>
                  <span className={passed ? 'text-risk-low' : 'text-text-muted'}>
                    {req.label}
                  </span>
                </div>
              );
            })}
          </motion.div>
        )}

        <FloatingInput
          label="Confirm password"
          type="password"
          icon={<Lock className="w-5 h-5" />}
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        <Button
          type="submit"
          loading={isLoading}
          className="w-full"
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Create account
        </Button>
      </form>

      {/* Terms */}
      <p className="text-xs text-text-muted text-center">
        By creating an account, you agree to our{' '}
        <Link href="/terms" className="text-brand-teal hover:underline">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="/privacy" className="text-brand-teal hover:underline">
          Privacy Policy
        </Link>
      </p>

      {/* Login link */}
      <p className="text-center text-text-secondary">
        Already have an account?{' '}
        <Link
          href="/auth/login"
          className="text-brand-teal hover:text-brand-tealDim font-medium transition-colors"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
