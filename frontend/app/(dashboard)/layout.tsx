'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store';
import { DashboardLayout } from '@/components/layout';
import { Spinner } from '@/components/ui';

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, hydrated, user } = useAuthStore();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (hydrated) {
      if (!isAuthenticated) {
        router.replace(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
      } else if (!user?.onboarding_completed && pathname !== '/onboarding') {
        router.replace('/onboarding');
      } else {
        setIsReady(true);
      }
    }
  }, [hydrated, isAuthenticated, user, pathname, router]);

  if (!hydrated || !isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-base">
        <div className="flex flex-col items-center gap-4">
          <Spinner size="lg" />
          <p className="text-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  return <DashboardLayout>{children}</DashboardLayout>;
}
