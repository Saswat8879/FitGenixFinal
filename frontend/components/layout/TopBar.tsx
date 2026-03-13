'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, Bell, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useAuthStore, useUIStore } from '@/store';
import { cn, getGreeting } from '@/lib/utils';

export function TopBar() {
  const { user, logout } = useAuthStore();
  const { setSidebarOpen } = useUIStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const greeting = getGreeting();

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 lg:px-6 bg-white/55 backdrop-blur-xl border-b border-white/70 shadow-[0_8px_30px_rgba(15,23,42,0.08)]">
      {/* Left side */}
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden p-2 text-text-muted hover:text-text-primary hover:bg-white/60 rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Greeting */}
        <div className="hidden sm:block">
          <p className="text-sm text-text-secondary">{greeting}</p>
          <p className="text-lg font-semibold text-text-primary">
            {user?.full_name?.split(' ')[0] || user?.name || 'User'}
          </p>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative p-2 text-text-muted hover:text-text-primary hover:bg-white/60 rounded-lg transition-colors"
          >
            <Bell className="w-5 h-5" />
            {/* Notification badge */}
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand-teal rounded-full" />
          </button>

          <AnimatePresence>
            {notificationsOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setNotificationsOpen(false)}
                />
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-80 py-2 bg-white/85 backdrop-blur-xl border border-white/75 rounded-xl shadow-xl z-50"
                >
                  <div className="px-4 py-2 border-b border-bg-border">
                    <h3 className="font-semibold text-text-primary">Notifications</h3>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    <div className="px-4 py-6 text-center text-text-muted text-sm">
                      No new notifications
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>

        {/* User dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 p-1.5 pl-2 pr-3 text-text-secondary hover:text-text-primary hover:bg-white/60 rounded-full transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center">
              <span className="text-white text-sm font-semibold">
                {user?.full_name?.[0]?.toUpperCase() || user?.name?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <ChevronDown className={cn(
              'w-4 h-4 transition-transform',
              dropdownOpen && 'rotate-180'
            )} />
          </button>

          <AnimatePresence>
            {dropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setDropdownOpen(false)}
                />
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-2 w-56 py-2 bg-white/88 backdrop-blur-xl border border-white/75 rounded-xl shadow-xl z-50"
                >
                  <div className="px-4 py-2 border-b border-bg-border">
                    <p className="font-semibold text-text-primary">
                      {user?.full_name || user?.name}
                    </p>
                    <p className="text-sm text-text-muted truncate">{user?.email}</p>
                  </div>

                  <div className="py-1">
                    <Link
                      href="/profile"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-text-secondary hover:text-text-primary hover:bg-white/60 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      <span>Profile</span>
                    </Link>
                    <Link
                      href="/profile?tab=settings"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 text-text-secondary hover:text-text-primary hover:bg-white/60 transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Settings</span>
                    </Link>
                  </div>

                  <div className="border-t border-bg-border pt-1">
                    <button
                      onClick={() => {
                        setDropdownOpen(false);
                        logout();
                      }}
                      className="flex items-center gap-3 w-full px-4 py-2 text-risk-high hover:bg-risk-high/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Log out</span>
                    </button>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
