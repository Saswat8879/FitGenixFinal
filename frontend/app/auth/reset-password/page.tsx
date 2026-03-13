'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { KeyRound, Lock, ArrowRight, ArrowLeft } from 'lucide-react';
import { authApi } from '@/api';
import { useUIStore } from '@/store';
import { Button } from '@/components/ui';
import { FloatingInput } from '@/components/forms';

const resetSchema = z
  .object({
    token: z.string().min(1, 'Reset token is required'),
    newPassword: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type ResetForm = z.infer<typeof resetSchema>;

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialToken = searchParams.get('token') || '';
  const { addToast } = useUIStore();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
    defaultValues: {
      token: initialToken,
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ResetForm) => {
    setIsSubmitting(true);
    try {
      const res = await authApi.resetPassword({
        token: data.token,
        new_password: data.newPassword,
      });
      addToast({ type: 'success', message: res.message || 'Password reset successful' });
      router.push('/auth/login');
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      addToast({
        type: 'error',
        message: typeof detail === 'string' ? detail : 'Failed to reset password',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center lg:text-left">
        <h2 className="text-3xl font-bold text-text-primary mb-2">Reset password</h2>
        <p className="text-text-secondary">Enter your reset token and set a new password.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FloatingInput
          label="Reset token"
          type="text"
          icon={<KeyRound className="w-5 h-5" />}
          error={errors.token?.message}
          {...register('token')}
        />

        <FloatingInput
          label="New password"
          type="password"
          icon={<Lock className="w-5 h-5" />}
          error={errors.newPassword?.message}
          {...register('newPassword')}
        />

        <FloatingInput
          label="Confirm new password"
          type="password"
          icon={<Lock className="w-5 h-5" />}
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        <Button
          type="submit"
          loading={isSubmitting}
          className="w-full"
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Reset password
        </Button>
      </form>

      <Link
        href="/auth/login"
        className="inline-flex items-center gap-2 text-brand-teal hover:text-brand-tealDim transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to login
      </Link>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="text-text-secondary">Loading reset page...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
