'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dumbbell,
  Clock,
  Flame,
  Play,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Star,
  Timer,
  Target,
} from 'lucide-react';
import { plansApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  Modal,
  ProgressBar,
} from '@/components/ui';
import { RatingStars, TextArea } from '@/components/forms';
import { cn, roundCalories } from '@/lib/utils';
import type { Exercise } from '@/lib/types';

export default function WorkoutPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  const [expandedExercise, setExpandedExercise] = useState<number | null>(null);
  const [isWorkoutActive, setIsWorkoutActive] = useState(false);
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [completedExercises, setCompletedExercises] = useState<Set<number>>(new Set());
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(4);
  const [feedbackNote, setFeedbackNote] = useState('');

  const { data: workout, isLoading } = useQuery({
    queryKey: ['workout', 'today'],
    queryFn: plansApi.getTodayWorkout,
  });

  const completeMutation = useMutation({
    mutationFn: () => plansApi.completeWorkout(workout?.id || 0),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workout'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Workout completed! Great job!' });
      setIsWorkoutActive(false);
      setShowFeedbackModal(true);
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: () => plansApi.submitWorkoutFeedback(workout?.id || 0, {
      completed: true,
      rating: feedbackRating,
      difficulty_rating: feedbackRating,
      notes: feedbackNote,
    }),
    onSuccess: () => {
      addToast({ type: 'success', message: 'Feedback submitted! We\'ll adjust your future workouts.' });
      setShowFeedbackModal(false);
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: () => plansApi.regeneratePlans(true, false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workout'] });
      addToast({ type: 'success', message: 'New workout plan generated!' });
    },
  });

  const handleStartWorkout = () => {
    setIsWorkoutActive(true);
    setCurrentExerciseIndex(0);
    setCompletedExercises(new Set());
  };

  const handleCompleteExercise = (index: number) => {
    const newCompleted = new Set(completedExercises);
    newCompleted.add(index);
    setCompletedExercises(newCompleted);

    if (index < (workout?.exercises?.length || 0) - 1) {
      setCurrentExerciseIndex(index + 1);
    }
  };

  const handleFinishWorkout = () => {
    completeMutation.mutate();
  };

  const progress = workout?.exercises
    ? (completedExercises.size / workout.exercises.length) * 100
    : 0;

  if (isLoading) {
    return (
      <PageTransition className="space-y-6">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-48 skeleton rounded-xl" />
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 skeleton rounded-xl" />
          ))}
        </div>
      </PageTransition>
    );
  }

  if (!workout) {
    return (
      <PageTransition>
        <div className="text-center py-12">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-bg-elevated flex items-center justify-center">
            <Dumbbell className="w-10 h-10 text-text-muted" />
          </div>
          <h2 className="text-2xl font-bold text-text-primary mb-2">No Workout Today</h2>
          <p className="text-text-secondary mb-6">
            You don't have a workout scheduled for today, or your plan hasn't been generated yet.
          </p>
          <Button
            onClick={() => regenerateMutation.mutate()}
            loading={regenerateMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Generate Workout Plan
          </Button>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <SectionHeading
            title={workout.name || "Today's Workout"}
            subtitle={workout.description}
            className="mb-0"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => regenerateMutation.mutate()}
            loading={regenerateMutation.isPending}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Regenerate
          </Button>
        </div>

        {/* Workout overview card */}
        <GlowCard>
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-text-secondary">
                <Target className="w-5 h-5 text-brand-teal" />
                <span>{workout.exercises?.length || 0} exercises</span>
              </div>
              <div className="flex items-center gap-2 text-text-secondary">
                <Clock className="w-5 h-5 text-blue-400" />
                <span>{workout.duration_minutes} min</span>
              </div>
              <div className="flex items-center gap-2 text-text-secondary">
                <Flame className="w-5 h-5 text-orange-400" />
                <span>~{roundCalories(workout.estimated_calories)} cal</span>
              </div>
            </div>
            {!isWorkoutActive && !workout.completed ? (
              <Button onClick={handleStartWorkout} icon={<Play className="w-4 h-4" />}>
                Start Workout
              </Button>
            ) : workout.completed ? (
              <div className="flex items-center gap-2 text-risk-low">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">Completed</span>
              </div>
            ) : null}
          </div>

          {isWorkoutActive && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">Progress</span>
                <span className="text-brand-teal font-medium">
                  {completedExercises.size} / {workout.exercises?.length || 0}
                </span>
              </div>
              <ProgressBar value={progress} />
            </div>
          )}
        </GlowCard>

        {/* Exercise list */}
        <div className="space-y-3">
          {workout.exercises?.map((exercise: Exercise, index: number) => {
            const isExpanded = expandedExercise === index;
            const isCompleted = completedExercises.has(index);
            const isCurrent = isWorkoutActive && currentExerciseIndex === index;

            return (
              <motion.div
                key={exercise.id || index}
                layout
                className={cn(
                  'rounded-xl border transition-all',
                  isCompleted
                    ? 'bg-risk-low/10 border-risk-low/30'
                    : isCurrent
                    ? 'bg-brand-teal/10 border-brand-teal/30'
                    : 'bg-bg-card border-bg-border hover:border-bg-border/80'
                )}
              >
                <button
                  onClick={() => setExpandedExercise(isExpanded ? null : index)}
                  className="w-full p-4 flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold',
                        isCompleted
                          ? 'bg-risk-low text-white'
                          : isCurrent
                          ? 'bg-brand-teal text-white'
                          : 'bg-bg-elevated text-text-secondary'
                      )}
                    >
                      {isCompleted ? <CheckCircle className="w-5 h-5" /> : index + 1}
                    </div>
                    <div>
                      <h3 className="font-semibold text-text-primary">{exercise.name}</h3>
                      <p className="text-sm text-text-secondary">
                        {exercise.sets} sets × {exercise.reps} reps
                        {exercise.weight_kg && ` • ${exercise.weight_kg}kg`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {exercise.rest_seconds && (
                      <span className="text-sm text-text-muted flex items-center gap-1">
                        <Timer className="w-4 h-4" />
                        {exercise.rest_seconds}s rest
                      </span>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-text-muted" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-text-muted" />
                    )}
                  </div>
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 pt-0 border-t border-bg-border/50 mt-2">
                        <div className="pt-4 space-y-4">
                          {exercise.instructions && (
                            <div>
                              <h4 className="text-sm font-medium text-text-primary mb-2">
                                Instructions
                              </h4>
                              <p className="text-sm text-text-secondary">
                                {exercise.instructions}
                              </p>
                            </div>
                          )}
                          {exercise.target_muscles && exercise.target_muscles.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium text-text-primary mb-2">
                                Target Muscles
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {exercise.target_muscles.map((muscle: string) => (
                                  <span
                                    key={muscle}
                                    className="px-2 py-1 rounded-full bg-bg-elevated text-xs text-text-secondary"
                                  >
                                    {muscle}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {isWorkoutActive && !isCompleted && (
                            <Button
                              onClick={() => handleCompleteExercise(index)}
                              className="w-full"
                              icon={<CheckCircle className="w-4 h-4" />}
                            >
                              Mark as Complete
                            </Button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>

        {/* Finish workout button */}
        {isWorkoutActive && completedExercises.size === (workout.exercises?.length || 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <Button
              size="lg"
              onClick={handleFinishWorkout}
              loading={completeMutation.isPending}
              icon={<CheckCircle className="w-5 h-5" />}
            >
              Finish Workout
            </Button>
          </motion.div>
        )}

        {/* Feedback modal */}
        <Modal
          isOpen={showFeedbackModal}
          onClose={() => setShowFeedbackModal(false)}
          title="How was your workout?"
          size="sm"
        >
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-risk-low/10 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-risk-low" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary">Great job!</h3>
              <p className="text-text-secondary">
                You completed {workout.exercises?.length || 0} exercises
              </p>
            </div>

            <RatingStars
              value={feedbackRating}
              onChange={setFeedbackRating}
              label="Rate this workout"
              size="lg"
            />

            <TextArea
              label="Any notes? (optional)"
              value={feedbackNote}
              onChange={(e) => setFeedbackNote(e.target.value)}
              placeholder="Was it too easy? Too hard? Let us know..."
              rows={3}
            />

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowFeedbackModal(false)}
              >
                Skip
              </Button>
              <Button
                className="flex-1"
                onClick={() => feedbackMutation.mutate()}
                loading={feedbackMutation.isPending}
              >
                Submit Feedback
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </PageTransition>
  );
}
