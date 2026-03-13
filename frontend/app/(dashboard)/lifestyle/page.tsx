'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Brain,
  Heart,
  Moon,
  Smile,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Lightbulb,
  Activity,
} from 'lucide-react';
import { lifestyleApi } from '@/api';
import { useUIStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  AnimatedNumber,
  Button,
  RiskBadge,
  Modal,
} from '@/components/ui';
import { GaugeArc, LineChart } from '@/components/charts';
import { Slider, RatingStars, TextArea } from '@/components/forms';
import { cn, getRiskLevel } from '@/lib/utils';

export default function LifestylePage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  const [showStressModal, setShowStressModal] = useState(false);
  const [showCheckinModal, setShowCheckinModal] = useState(false);
  
  // Stress check form
  const [heartRate, setHeartRate] = useState(75);
  const [sleepHours, setSleepHours] = useState(7);
  const [perceivedStress, setPerceivedStress] = useState(5);
  const [notes, setNotes] = useState('');

  // Daily checkin form
  const [mood, setMood] = useState(4);
  const [energy, setEnergy] = useState(3);
  const [anxiety, setAnxiety] = useState(2);
  const [sleepQuality, setSleepQuality] = useState(4);

  const { data: tips } = useQuery({
    queryKey: ['lifestyle', 'tips'],
    queryFn: lifestyleApi.getTips,
  });

  const { data: posture } = useQuery({
    queryKey: ['lifestyle', 'posture'],
    queryFn: lifestyleApi.getPosture,
  });

  const stressCheckMutation = useMutation({
    mutationFn: () => lifestyleApi.stressCheck({
      heart_rate: heartRate,
      sleep_hours: sleepHours,
      perceived_stress: perceivedStress,
      notes,
    }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ 
        type: data.stress_level > 7 ? 'warning' : 'success',
        message: `Stress level: ${data.stress_level}/10. ${data.recommendation || ''}` 
      });
      setShowStressModal(false);
    },
  });

  const checkinMutation = useMutation({
    mutationFn: () => lifestyleApi.checkin({
      mood,
      energy_level: energy,
      anxiety_level: anxiety,
      sleep_quality: sleepQuality,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['lifestylePoints'] });
      addToast({ type: 'success', message: 'Daily check-in recorded!' });
      setShowCheckinModal(false);
    },
  });

  return (
    <PageTransition>
      <div className="space-y-6">
        <SectionHeading
          title="Lifestyle & Wellness"
          subtitle="Monitor your stress, mood, and daily habits"
        />

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <GlowCard className="cursor-pointer" onClick={() => setShowStressModal(true)}>
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-sky-500/10 flex items-center justify-center">
                <Brain className="w-7 h-7 text-sky-500" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-text-primary">Stress Check</h3>
                <p className="text-sm text-text-secondary">
                  Analyze your current stress level
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-text-muted" />
            </div>
          </GlowCard>

          <GlowCard className="cursor-pointer" onClick={() => setShowCheckinModal(true)}>
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-brand-teal/10 flex items-center justify-center">
                <Smile className="w-7 h-7 text-brand-teal" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-text-primary">Daily Check-in</h3>
                <p className="text-sm text-text-secondary">
                  Log your mood and energy levels
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-text-muted" />
            </div>
          </GlowCard>
        </div>

        {/* Wellness tips */}
        {tips?.tips && tips.tips.length > 0 && (
          <GlowCard>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-yellow-400" />
              <h3 className="font-semibold text-text-primary">Today's Wellness Tips</h3>
            </div>
            <div className="space-y-3">
              {tips.tips.map((tip: string, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3 p-3 rounded-lg bg-bg-elevated"
                >
                  <div className="w-6 h-6 rounded-full bg-brand-teal/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-brand-teal">{i + 1}</span>
                  </div>
                  <p className="text-sm text-text-secondary">{tip}</p>
                </motion.div>
              ))}
            </div>
          </GlowCard>
        )}

        {/* Posture reminder */}
        {posture && (
          <GlowCard>
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-blue-400" />
              <h3 className="font-semibold text-text-primary">Posture & Movement</h3>
            </div>
            <div className="p-4 rounded-lg bg-bg-elevated">
              <p className="text-text-secondary">{posture.message}</p>
              {posture.exercise && (
                <div className="mt-3 p-3 rounded-lg bg-bg-card border border-bg-border">
                  <h4 className="font-medium text-text-primary">{posture.exercise.name}</h4>
                  <p className="text-sm text-text-muted mt-1">{posture.exercise.description}</p>
                </div>
              )}
            </div>
          </GlowCard>
        )}

        {/* Stress check modal */}
        <Modal
          isOpen={showStressModal}
          onClose={() => setShowStressModal(false)}
          title="Stress Analysis"
          size="md"
        >
          <div className="space-y-6">
            <div className="text-center p-4 rounded-lg bg-sky-500/10 border border-sky-500/30">
              <Brain className="w-10 h-10 text-sky-500 mx-auto mb-2" />
              <p className="text-sm text-text-secondary">
                Answer a few questions to analyze your current stress level
              </p>
            </div>

            <Slider
              label="Current Heart Rate (BPM)"
              value={heartRate}
              onChange={setHeartRate}
              min={50}
              max={150}
              formatValue={(v) => `${v} BPM`}
            />

            <Slider
              label="Hours of Sleep Last Night"
              value={sleepHours}
              onChange={setSleepHours}
              min={0}
              max={12}
              step={0.5}
              formatValue={(v) => `${v} hours`}
            />

            <Slider
              label="Perceived Stress Level"
              value={perceivedStress}
              onChange={setPerceivedStress}
              min={1}
              max={10}
              marks={[
                { value: 1, label: 'Calm' },
                { value: 5, label: 'Moderate' },
                { value: 10, label: 'High' },
              ]}
            />

            <TextArea
              label="Additional Notes (optional)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any context about how you're feeling..."
              rows={2}
            />

            <Button
              className="w-full"
              onClick={() => stressCheckMutation.mutate()}
              loading={stressCheckMutation.isPending}
            >
              Analyze Stress Level
            </Button>
          </div>
        </Modal>

        {/* Daily checkin modal */}
        <Modal
          isOpen={showCheckinModal}
          onClose={() => setShowCheckinModal(false)}
          title="Daily Check-in"
          size="md"
        >
          <div className="space-y-6">
            <RatingStars
              label="How's your mood today?"
              value={mood}
              onChange={setMood}
              size="lg"
            />

            <Slider
              label="Energy Level"
              value={energy}
              onChange={setEnergy}
              min={1}
              max={5}
              marks={[
                { value: 1, label: 'Low' },
                { value: 3, label: 'Normal' },
                { value: 5, label: 'High' },
              ]}
            />

            <Slider
              label="Anxiety Level"
              value={anxiety}
              onChange={setAnxiety}
              min={1}
              max={5}
              marks={[
                { value: 1, label: 'None' },
                { value: 3, label: 'Some' },
                { value: 5, label: 'High' },
              ]}
            />

            <Slider
              label="Sleep Quality"
              value={sleepQuality}
              onChange={setSleepQuality}
              min={1}
              max={5}
              marks={[
                { value: 1, label: 'Poor' },
                { value: 3, label: 'Okay' },
                { value: 5, label: 'Great' },
              ]}
            />

            <Button
              className="w-full"
              onClick={() => checkinMutation.mutate()}
              loading={checkinMutation.isPending}
            >
              Submit Check-in
            </Button>
          </div>
        </Modal>
      </div>
    </PageTransition>
  );
}
