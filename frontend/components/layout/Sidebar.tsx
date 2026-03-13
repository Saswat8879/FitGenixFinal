'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Dumbbell,
  Utensils,
  ClipboardList,
  Brain,
  TrendingUp,
  Heart,
  MessageSquare,
  Users,
  Watch,
  User,
  FlaskConical,
  Sparkles,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore, useAuthStore } from '@/store';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { href: '/workout', label: 'Workout', icon: <Dumbbell className="w-5 h-5" /> },
  { href: '/diet', label: 'Diet', icon: <Utensils className="w-5 h-5" /> },
  { href: '/logs', label: 'Logs', icon: <ClipboardList className="w-5 h-5" /> },
  { href: '/lifestyle', label: 'Lifestyle', icon: <Brain className="w-5 h-5" /> },
  { href: '/lifestyle-points', label: 'Lifestyle Points', icon: <Sparkles className="w-5 h-5" /> },
  { href: '/progress', label: 'Progress', icon: <TrendingUp className="w-5 h-5" /> },
  { href: '/health', label: 'Health', icon: <Heart className="w-5 h-5" /> },
  { href: '/chat', label: 'AI Coach', icon: <MessageSquare className="w-5 h-5" /> },
  { href: '/community', label: 'Community', icon: <Users className="w-5 h-5" /> },
  { href: '/fit', label: 'Fit Connect', icon: <Watch className="w-5 h-5" /> },
  { href: '/profile', label: 'Profile', icon: <User className="w-5 h-5" /> },
  { href: '/simulate', label: 'Simulate', icon: <FlaskConical className="w-5 h-5" />, adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();
  const { isAdmin } = useAuthStore();

  const filteredItems = navItems.filter(item => !item.adminOnly || isAdmin);

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 bg-white/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        className={cn(
          'fixed top-0 left-0 h-screen z-50 flex flex-col',
          'bg-white/66 backdrop-blur-xl border-r border-white/70 shadow-[0_14px_40px_rgba(15,23,42,0.1)]',
          'lg:relative lg:z-30'
        )}
        initial={false}
        animate={{
          width: sidebarOpen ? 256 : 72,
          x: sidebarOpen ? 0 : 0,
        }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-bg-border">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl border border-white/75 bg-white/75 backdrop-blur-md flex items-center justify-center flex-shrink-0 overflow-hidden">
              <Image
                src="/assets/mascot.png"
                alt="FitGenix mascot"
                width={40}
                height={40}
                className="w-full h-full object-cover"
                priority
              />
            </div>
            <AnimatePresence mode="wait">
              {sidebarOpen && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="font-bold text-xl text-text-primary whitespace-nowrap"
                >
                  FitGenix
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
          
          {/* Mobile close button */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 text-text-muted hover:text-text-primary"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 scrollbar-thin scrollbar-thumb-bg-border">
          <ul className="space-y-1 px-3">
            {filteredItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => {
                      if (window.innerWidth < 1024) {
                        setSidebarOpen(false);
                      }
                    }}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative',
                      isActive
                        ? 'bg-brand-teal/12 text-brand-teal'
                        : 'text-text-secondary hover:text-text-primary hover:bg-white/60'
                    )}
                  >
                    {/* Active indicator */}
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-brand-teal rounded-r-full"
                        transition={{ duration: 0.2 }}
                      />
                    )}
                    
                    <span className={cn(
                      'flex-shrink-0 transition-transform group-hover:scale-110',
                      isActive && 'text-brand-teal'
                    )}>
                      {item.icon}
                    </span>
                    
                    <AnimatePresence mode="wait">
                      {sidebarOpen && (
                        <motion.span
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          className="whitespace-nowrap font-medium"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Collapse toggle (desktop only) */}
        <div className="hidden lg:flex items-center justify-center p-4 border-t border-bg-border">
          <button
            onClick={toggleSidebar}
            className="p-2 text-text-muted hover:text-text-primary hover:bg-white/60 rounded-lg transition-colors"
          >
            {sidebarOpen ? (
              <ChevronLeft className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
        </div>
      </motion.aside>
    </>
  );
}

export default Sidebar;
