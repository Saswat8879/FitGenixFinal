'use client';

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  User,
  Mail,
  Settings,
  LogOut,
  Edit3,
  Save,
  X,
  Camera,
} from 'lucide-react';
import { profileApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  Button,
  Toggle,
  Tabs,
} from '@/components/ui';
import { FloatingInput, TileSelect, NumberStepper } from '@/components/forms';
import { GOALS, ACTIVITY_LEVELS, COACHING_STYLES, DIET_TYPES } from '@/lib/utils';

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { user, logout } = useAuthStore();
  const { addToast } = useUIStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  
  // Profile form state
  const [fullName, setFullName] = useState(user?.name || '');
  const [heightCm, setHeightCm] = useState(170);
  const [weightKg, setWeightKg] = useState(70);
  const [age, setAge] = useState(30);

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => profileApi.getProfile(),
  });

  useEffect(() => {
    if (!profile) return;
    setFullName(profile.name || user?.name || '');
    setHeightCm(profile.height_cm ?? 170);
    setWeightKg(profile.weight_kg ?? 70);
    setAge(profile.age ?? 30);
  }, [profile, user?.name]);

  // Update profile mutations
  const updatePersonalMutation = useMutation({
    mutationFn: (data: { name?: string; height_cm?: number; weight_kg?: number; age?: number }) =>
      profileApi.updatePersonal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      addToast({ type: 'success', message: 'Profile updated!' });
      setIsEditing(false);
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to update profile' });
    },
  });

  const updateGoalsMutation = useMutation({
    mutationFn: (data: { goal?: string; coaching_style?: string; activity_level?: string }) =>
      profileApi.updateGoals(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      addToast({ type: 'success', message: 'Goals updated!' });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to update goals' });
    },
  });

  const updateDietMutation = useMutation({
    mutationFn: (data: { diet_type?: string }) =>
      profileApi.updateDiet(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      addToast({ type: 'success', message: 'Diet preferences updated!' });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to update diet preferences' });
    },
  });

  const updateNotificationsMutation = useMutation({
    mutationFn: (data: { preferred_notifications: boolean }) =>
      profileApi.updateNotifications(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      addToast({ type: 'success', message: 'Notification settings updated!' });
    },
    onError: () => {
      addToast({ type: 'error', message: 'Failed to update notifications' });
    },
  });

  const handleLogout = () => {
    logout();
    window.location.href = '/auth/login';
  };

  const handleSaveProfile = () => {
    updatePersonalMutation.mutate({
      name: fullName,
      height_cm: heightCm,
      weight_kg: weightKg,
      age: age,
    });
  };

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-64 skeleton rounded-xl" />
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Profile & Settings"
          subtitle="Manage your account and preferences"
        />

        <Tabs
          tabs={[
            { id: 'profile', label: 'Profile' },
            { id: 'preferences', label: 'Preferences' },
            { id: 'notifications', label: 'Notifications' },
            { id: 'account', label: 'Account' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {activeTab === 'profile' && (
          <div className="space-y-6">
            {/* Profile card */}
            <GlowCard>
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center">
                      <span className="text-3xl font-bold text-white">
                        {(profile?.name || user?.name || 'U').charAt(0)}
                      </span>
                    </div>
                    <button className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-bg-surface border border-bg-border flex items-center justify-center hover:bg-bg-elevated transition-colors">
                      <Camera className="w-4 h-4 text-text-secondary" />
                    </button>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-text-primary">
                      {profile?.name || user?.name || 'User'}
                    </h3>
                    <p className="text-text-secondary">{profile?.email || user?.email}</p>
                    {user?.is_admin && (
                      <span className="inline-block mt-1 px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-500 text-xs">
                        Admin
                      </span>
                    )}
                  </div>
                </div>
                <Button
                  variant={isEditing ? 'primary' : 'outline'}
                  onClick={() => {
                    if (isEditing) {
                      handleSaveProfile();
                    } else {
                      setIsEditing(true);
                    }
                  }}
                  loading={updatePersonalMutation.isPending}
                  icon={isEditing ? <Save className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
                >
                  {isEditing ? 'Save' : 'Edit'}
                </Button>
              </div>

              <div className="space-y-4">
                <FloatingInput
                  label="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={!isEditing}
                  icon={<User className="w-4 h-4" />}
                />
                <FloatingInput
                  label="Email"
                  type="email"
                  value={user?.email || ''}
                  disabled
                  icon={<Mail className="w-4 h-4" />}
                />
                {isEditing && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <NumberStepper
                        label="Height (cm)"
                        value={heightCm}
                        onChange={setHeightCm}
                        min={120}
                        max={220}
                      />
                      <NumberStepper
                        label="Weight (kg)"
                        value={weightKg}
                        onChange={setWeightKg}
                        min={30}
                        max={200}
                      />
                    </div>
                    <NumberStepper
                      label="Age"
                      value={age}
                      onChange={setAge}
                      min={18}
                      max={100}
                    />
                    <Button
                      variant="ghost"
                      onClick={() => setIsEditing(false)}
                      icon={<X className="w-4 h-4" />}
                    >
                      Cancel
                    </Button>
                  </>
                )}
              </div>
            </GlowCard>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <GlowCard className="text-center py-4">
                <p className="text-2xl font-bold text-brand-teal">{profile?.workouts_completed || 0}</p>
                <p className="text-sm text-text-muted">Workouts</p>
              </GlowCard>
              <GlowCard className="text-center py-4">
                <p className="text-2xl font-bold text-sky-500">{profile?.streak || 0}</p>
                <p className="text-sm text-text-muted">Day Streak</p>
              </GlowCard>
              <GlowCard className="text-center py-4">
                <p className="text-2xl font-bold text-orange-400">{profile?.total_points || 0}</p>
                <p className="text-sm text-text-muted">Total Points</p>
              </GlowCard>
            </div>
          </div>
        )}

        {activeTab === 'preferences' && (
          <div className="space-y-6">
            <GlowCard>
              <SectionHeading title="Fitness Preferences" className="mb-4" />
              <div className="space-y-6">
                <TileSelect
                  label="Primary Goal"
                  options={GOALS}
                  value={profile?.goal || 'lose_weight'}
                  onChange={(v) => updateGoalsMutation.mutate({ goal: v as string })}
                />
                <TileSelect
                  label="Activity Level"
                  options={ACTIVITY_LEVELS}
                  value={profile?.activity_level || 'sedentary'}
                  onChange={(v) => updateGoalsMutation.mutate({ activity_level: v as string })}
                />
                <TileSelect
                  label="Diet Type"
                  options={DIET_TYPES}
                  value={profile?.diet_type || 'non_vegetarian'}
                  onChange={(v) => updateDietMutation.mutate({ diet_type: v as string })}
                />
                <TileSelect
                  label="Coaching Style"
                  options={COACHING_STYLES}
                  value={profile?.coaching_style || 'moderate'}
                  onChange={(v) => updateGoalsMutation.mutate({ coaching_style: v as string })}
                />
              </div>
            </GlowCard>
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <GlowCard>
              <SectionHeading title="Notification Settings" className="mb-4" />
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-bg-elevated">
                  <div>
                    <p className="font-medium text-text-primary">Enable Notifications</p>
                    <p className="text-sm text-text-muted">Receive workout, meal, and progress reminders</p>
                  </div>
                  <Toggle
                    checked={profile?.preferred_notifications ?? true}
                    onChange={(v) => updateNotificationsMutation.mutate({ preferred_notifications: v })}
                  />
                </div>
              </div>
            </GlowCard>
          </div>
        )}

        {activeTab === 'account' && (
          <div className="space-y-6">
            <GlowCard>
              <SectionHeading title="Account Information" className="mb-4" />
              <div className="space-y-4 text-sm">
                <div className="flex justify-between p-3 rounded-lg bg-bg-elevated">
                  <span className="text-text-muted">Email</span>
                  <span className="text-text-primary">{profile?.email || user?.email}</span>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-bg-elevated">
                  <span className="text-text-muted">Account Type</span>
                  <span className="text-text-primary">{user?.is_admin ? 'Admin' : 'User'}</span>
                </div>
              </div>
            </GlowCard>

            <GlowCard>
              <SectionHeading title="Account Actions" className="mb-4" />
              <Button
                variant="outline"
                className="w-full border-red-500/30 text-red-400 hover:bg-red-500/10"
                onClick={handleLogout}
                icon={<LogOut className="w-4 h-4" />}
              >
                Sign Out
              </Button>
            </GlowCard>
          </div>
        )}
      </div>
    </PageTransition>
  );
}
