'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, Target, Dumbbell, Utensils, Heart, Brain } from 'lucide-react';
import { onboardingApi } from '@/api';
import { useAuthStore, useUIStore } from '@/store';
import { Button, ProgressBar } from '@/components/ui';
import { TileSelect, NumberStepper, Slider, ToggleChip } from '@/components/forms';
import { GOALS, ACTIVITY_LEVELS, COACHING_STYLES, DIET_TYPES, WORK_STYLES, EQUIPMENT_OPTIONS, MEDICAL_CONDITIONS } from '@/lib/utils';

const steps = [
  { id: 'goals', title: 'Your Goals', icon: <Target className="w-6 h-6" /> },
  { id: 'body', title: 'Body Metrics', icon: <Dumbbell className="w-6 h-6" /> },
  { id: 'lifestyle', title: 'Lifestyle', icon: <Brain className="w-6 h-6" /> },
  { id: 'diet', title: 'Diet Preferences', icon: <Utensils className="w-6 h-6" /> },
  { id: 'health', title: 'Health', icon: <Heart className="w-6 h-6" /> },
];

interface FormData {
  goal: string;
  activityLevel: string;
  coachingStyle: string;
  age: number;
  sex: string;
  weight: number;
  height: number;
  targetWeight: number;
  workStyle: string;
  dietType: string;
  equipment: string[];
  timeAvailableMin: number;
  medicalConditions: string[];
}

const defaultFormData: FormData = {
  goal: 'lose_weight',
  activityLevel: 'moderate',
  coachingStyle: 'moderate',
  age: 25,
  sex: 'male',
  weight: 70,
  height: 170,
  targetWeight: 65,
  workStyle: 'desk_job',
  dietType: 'non_vegetarian',
  equipment: ['dumbbells'],
  timeAvailableMin: 45,
  medicalConditions: [],
};

export default function OnboardingPage() {
  const router = useRouter();
  const { user, setUser } = useAuthStore();
  const { addToast } = useUIStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<FormData>(defaultFormData);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const progress = ((currentStep + 1) / steps.length) * 100;

  const updateField = <K extends keyof FormData>(field: K, value: FormData[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Convert medicalConditions array to individual boolean fields
      const conditionBooleans = MEDICAL_CONDITIONS.reduce((acc, c) => {
        acc[c.field] = formData.medicalConditions.includes(c.field);
        return acc;
      }, {} as Record<string, boolean>);

      await onboardingApi.submitSurvey({
        goal: formData.goal,
        activity_level: formData.activityLevel,
        coaching_style: formData.coachingStyle,
        age: formData.age,
        sex: formData.sex,
        weight_kg: formData.weight,
        height_cm: formData.height,
        work_style: formData.workStyle,
        diet_type: formData.dietType,
        equipment: formData.equipment,
        time_available_min: formData.timeAvailableMin,
        ...conditionBooleans,
      });

      // Update user as onboarding completed
      if (user) {
        setUser({ ...user, onboarding_completed: true });
      }

      addToast({ type: 'success', message: 'Profile setup complete! Generating your personalized plans...' });
      router.push('/dashboard');
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
          ? detail.map((e: any) => e.msg || String(e)).join(', ')
          : 'Failed to save preferences';
      addToast({ type: 'error', message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0: // Goals
        return (
          <div className="space-y-8">
            <TileSelect
              label="What's your primary fitness goal?"
              options={GOALS.map((g) => ({ value: g.value, label: g.label }))}
              value={formData.goal}
              onChange={(v) => updateField('goal', v as string)}
              columns={2}
            />
            <TileSelect
              label="How active are you currently?"
              options={ACTIVITY_LEVELS.map((a) => ({ value: a.value, label: a.label }))}
              value={formData.activityLevel}
              onChange={(v) => updateField('activityLevel', v as string)}
              columns={2}
            />
            <TileSelect
              label="What coaching style do you prefer?"
              options={COACHING_STYLES.map((c) => ({ value: c.value, label: c.label }))}
              value={formData.coachingStyle}
              onChange={(v) => updateField('coachingStyle', v as string)}
              columns={3}
            />
          </div>
        );

      case 1: // Body Metrics
        return (
          <div className="space-y-8">
            <TileSelect
              label="Biological Sex"
              options={[
                { value: 'male', label: 'Male' },
                { value: 'female', label: 'Female' },
                { value: 'other', label: 'Prefer not to say' },
              ]}
              value={formData.sex}
              onChange={(v) => updateField('sex', v as string)}
              columns={3}
            />
            <div className="grid grid-cols-2 gap-6">
              <NumberStepper
                label="Age"
                value={formData.age}
                onChange={(v) => updateField('age', v)}
                min={13}
                max={100}
                unit=" yrs"
                size="lg"
              />
              <NumberStepper
                label="Height"
                value={formData.height}
                onChange={(v) => updateField('height', v)}
                min={100}
                max={250}
                unit=" cm"
                size="lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-6">
              <NumberStepper
                label="Current Weight"
                value={formData.weight}
                onChange={(v) => updateField('weight', v)}
                min={30}
                max={250}
                unit=" kg"
                size="lg"
              />
              <NumberStepper
                label="Target Weight"
                value={formData.targetWeight}
                onChange={(v) => updateField('targetWeight', v)}
                min={30}
                max={250}
                unit=" kg"
                size="lg"
              />
            </div>
          </div>
        );

      case 2: // Lifestyle
        return (
          <div className="space-y-8">
            <TileSelect
              label="What's your work style?"
              options={WORK_STYLES.map((w) => ({ value: w.value, label: w.label }))}
              value={formData.workStyle}
              onChange={(v) => updateField('workStyle', v as string)}
              columns={2}
            />
          </div>
        );

      case 3: // Diet
        return (
          <div className="space-y-8">
            <TileSelect
              label="What's your diet preference?"
              options={DIET_TYPES.map((d) => ({ value: d.value, label: d.label }))}
              value={formData.dietType}
              onChange={(v) => updateField('dietType', v as string)}
              columns={2}
            />
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-3">
                Available workout equipment (select all that apply)
              </label>
              <div className="flex flex-wrap gap-2">
                {EQUIPMENT_OPTIONS.map((eq) => (
                  <ToggleChip
                    key={eq}
                    label={eq}
                    selected={formData.equipment.includes(eq)}
                    onChange={(selected) => {
                      if (selected) {
                        updateField('equipment', [...formData.equipment, eq]);
                      } else {
                        updateField(
                          'equipment',
                          formData.equipment.filter((e) => e !== eq)
                        );
                      }
                    }}
                  />
                ))}
              </div>
            </div>
            <Slider
              label="Minutes available per workout"
              value={formData.timeAvailableMin}
              onChange={(v) => updateField('timeAvailableMin', v)}
              min={15}
              max={120}
              step={5}
              formatValue={(v) => `${v} min`}
              marks={[
                { value: 15, label: '15m' },
                { value: 30, label: '30m' },
                { value: 60, label: '60m' },
                { value: 90, label: '90m' },
              ]}
            />
          </div>
        );

      case 4: // Health
        return (
          <div className="space-y-8">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-3">
                Do you have any of these health conditions? (select if applicable)
              </label>
              <div className="flex flex-wrap gap-2">
                {MEDICAL_CONDITIONS.map((condition) => (
                  <ToggleChip
                    key={condition.field}
                    label={condition.label}
                    selected={formData.medicalConditions.includes(condition.field)}
                    onChange={(selected) => {
                      if (selected) {
                        updateField('medicalConditions', [...formData.medicalConditions, condition.field]);
                      } else {
                        updateField(
                          'medicalConditions',
                          formData.medicalConditions.filter((c) => c !== condition.field)
                        );
                      }
                    }}
                  />
                ))}
              </div>
            </div>
            
            <div className="p-4 rounded-xl bg-brand-teal/10 border border-brand-teal/30">
              <p className="text-sm text-text-secondary">
                <strong className="text-brand-teal">Note:</strong> This information helps us personalize your experience.
                Always consult with a healthcare provider before starting any new fitness program.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: "url('/assets/background_onboarding.png')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-br from-white/80 via-sky-50/72 to-emerald-50/74" />

      <div className="relative z-10 min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between h-16 px-6 border-b border-white/70 bg-white/45 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-teal to-brand-tealDim flex items-center justify-center">
            <span className="text-white font-bold text-lg">F</span>
          </div>
          <span className="text-xl font-bold text-text-primary">FitGenix</span>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          {steps.map((step, i) => (
            <div
              key={step.id}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                i === currentStep
                  ? 'bg-brand-teal/10 text-brand-teal'
                  : i < currentStep
                  ? 'text-risk-low'
                  : 'text-text-muted'
              }`}
            >
              {i < currentStep ? (
                <Check className="w-4 h-4" />
              ) : (
                <span className="w-4 h-4 text-center">{i + 1}</span>
              )}
              <span className="hidden md:inline">{step.title}</span>
            </div>
          ))}
        </div>
      </header>

      {/* Progress bar */}
      <div className="px-6 py-2 bg-white/30 backdrop-blur-sm border-b border-white/55">
        <ProgressBar value={progress} size="sm" />
      </div>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-2xl rounded-3xl glass p-6 sm:p-8 md:p-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Step header */}
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-xl bg-brand-teal/10 flex items-center justify-center text-brand-teal">
                  {steps[currentStep].icon}
                </div>
                <div>
                  <p className="text-sm text-text-muted">Step {currentStep + 1} of {steps.length}</p>
                  <h1 className="text-2xl font-bold text-text-primary">{steps[currentStep].title}</h1>
                </div>
              </div>

              {/* Step content */}
              {renderStep()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex items-center justify-between h-20 px-6 border-t border-white/70 bg-white/45 backdrop-blur-md">
        <Button
          variant="ghost"
          onClick={handleBack}
          disabled={currentStep === 0}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>
        <Button
          onClick={handleNext}
          loading={isSubmitting}
          icon={currentStep === steps.length - 1 ? <Check className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          {currentStep === steps.length - 1 ? 'Complete Setup' : 'Continue'}
        </Button>
      </footer>
      </div>
    </div>
  );
}
