'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Bot,
  User,
  Mic,
  MicOff,
  Trash2,
  Sparkles,
  Lightbulb,
} from 'lucide-react';
import { chatApi } from '@/api';
import { useUIStore, useAuthStore } from '@/store';
import {
  PageTransition,
  SectionHeading,
  GlowCard,
  Button,
  Spinner,
} from '@/components/ui';
import { TextArea } from '@/components/forms';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const QUICK_PROMPTS = [
  'What should I eat today?',
  'Give me a workout tip',
  'How can I reduce stress?',
  'Suggestions for better sleep',
];

export default function ChatPage() {
  const queryClient = useQueryClient();
  const { addToast } = useUIStore();
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load chat history
  const { data: history } = useQuery({
    queryKey: ['chat', 'history'],
    queryFn: () => chatApi.getHistory(),
  });

  useEffect(() => {
    if (history && history.length > 0) {
      setMessages(history.map((m) => ({
        id: String(m.id),
        role: m.role,
        content: m.message,
        timestamp: new Date(m.timestamp),
      })));
    }
  }, [history]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMutation = useMutation({
    mutationFn: (message: string) => chatApi.sendMessage(message),
    onMutate: (message) => {
      // Optimistically add user message
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsTyping(true);
    },
    onSuccess: (response) => {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response || 'I apologize, I could not process that request.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);
    },
    onError: (error) => {
      setIsTyping(false);
      addToast({ type: 'error', message: 'Failed to send message' });
    },
  });

  const clearMutation = useMutation({
    mutationFn: chatApi.clear,
    onSuccess: () => {
      setMessages([]);
      addToast({ type: 'success', message: 'Chat cleared' });
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    sendMutation.mutate(input.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <PageTransition className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <SectionHeading
          title="AI Coach"
          subtitle="Your personal fitness and wellness assistant"
          className="mb-0"
        />
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => clearMutation.mutate()}
            loading={clearMutation.isPending}
            icon={<Trash2 className="w-4 h-4" />}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Messages area */}
      <GlowCard className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-teal to-brand-teal/50 flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">
                Hi {user?.full_name?.split(' ')[0] || 'there'}!
              </h3>
              <p className="text-text-secondary max-w-md mb-8">
                I'm your AI fitness coach. Ask me anything about workouts, nutrition, 
                stress management, or your health goals!
              </p>

              {/* Quick prompts */}
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => {
                      setInput(prompt);
                      inputRef.current?.focus();
                    }}
                    className="px-4 py-2 rounded-full bg-bg-elevated border border-bg-border 
                             text-sm text-text-secondary hover:text-brand-teal hover:border-brand-teal/30
                             transition-all flex items-center gap-2"
                  >
                    <Lightbulb className="w-4 h-4" />
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={cn(
                      'flex gap-3',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-lg bg-brand-teal/10 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-brand-teal" />
                      </div>
                    )}
                    <div
                      className={cn(
                        'max-w-[75%] rounded-2xl px-4 py-3',
                        message.role === 'user'
                          ? 'bg-brand-teal text-white rounded-br-sm'
                          : 'bg-bg-elevated text-text-primary rounded-bl-sm'
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className={cn(
                        'text-xs mt-1',
                        message.role === 'user' ? 'text-white/60' : 'text-text-muted'
                      )}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-sky-500" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-lg bg-brand-teal/10 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-brand-teal" />
                  </div>
                  <div className="bg-bg-elevated rounded-2xl rounded-bl-sm px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input area */}
        <div className="border-t border-bg-border p-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                rows={1}
                className="w-full px-4 py-3 pr-12 bg-bg-elevated border border-bg-border rounded-xl
                         text-text-primary placeholder:text-text-muted resize-none
                         focus:outline-none focus:border-brand-teal/50 focus:ring-1 focus:ring-brand-teal/20
                         transition-all"
                style={{ maxHeight: '120px' }}
              />
            </div>
            <Button
              onClick={handleSend}
              disabled={!input.trim() || sendMutation.isPending}
              className="h-12 w-12 p-0"
            >
              {sendMutation.isPending ? (
                <Spinner size="sm" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
        </div>
      </GlowCard>
    </PageTransition>
  );
}
