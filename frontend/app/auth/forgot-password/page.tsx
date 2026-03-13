'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, ArrowRight, ArrowLeft } from 'lucide-react';
import { authApi } from '@/api';
import { useUIStore } from '@/store';
import { Button } from '@/components/ui';
import { FloatingInput } from '@/components/forms';

const forgotSchema = z.object({
  email: z.string().email('Please enter a valid email'),
});

type ForgotForm = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { addToast } = useUIStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resetUrl, setResetUrl] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (data: ForgotForm) => {
    setIsSubmitting(true);
    try {
      const res = await authApi.forgotPassword(data.email);
      setSubmitted(true);
      setResetUrl(res.reset_url || null);
      addToast({ type: 'success', message: res.message });

      // Local-dev convenience: auto-open reset page when backend returns token.
      if (res.reset_token) {
        router.push(`/auth/reset-password?token=${encodeURIComponent(res.reset_token)}`);
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      addToast({
        type: 'error',
        message: typeof detail === 'string' ? detail : 'Failed to process request',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="text-center lg:text-left">
        <h2 className="text-3xl font-bold text-text-primary mb-2">Forgot password?</h2>
        <p className="text-text-secondary">
          Enter your email and we will send you a reset link.
        </p>
      </div>

      {!submitted ? (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <FloatingInput
            label="Email"
            type="email"
            icon={<Mail className="w-5 h-5" />}
            error={errors.email?.message}
            {...register('email')}
          />

          <Button
            type="submit"
            loading={isSubmitting}
            className="w-full"
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Send reset link
          </Button>
        </form>
      ) : (
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-brand-teal/10 border border-brand-teal/30 text-sm text-text-secondary">
            If an account exists for that email, password reset instructions have been sent.
          </div>
          {resetUrl && (
            <div className="p-4 rounded-xl bg-bg-elevated border border-bg-border text-sm">
              <p className="text-text-secondary mb-2">Development reset link:</p>
              <a href={resetUrl} className="text-brand-teal hover:text-brand-tealDim break-all" target="_self" rel="noreferrer">
                {resetUrl}
              </a>
            </div>
          )}
        </div>
      )}

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
