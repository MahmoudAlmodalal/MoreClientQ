'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';
import { getDemoSession, sendDemoMessage, DemoSession } from '../../lib/demo-chat';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function LiveDemo() {
  const [session, setSession] = useState<DemoSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi there! I'm the platform's demo assistant. Ask me about multi-tenant security, custom Knowledge Bases (RAG), or our pricing plans!",
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load session info on mount
    setSession(getDemoSession());
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    if (session && session.messageCount >= 5) return;

    setErrorMsg(null);
    const userMessage = input.trim();
    setInput('');
    
    // Add User Message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsStreaming(true);

    // Add empty Assistant Message to append stream to
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    await sendDemoMessage(
      userMessage,
      (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg && lastMsg.role === 'assistant') {
            lastMsg.content += token;
          }
          return updated;
        });
      },
      () => {
        setIsStreaming(false);
        setSession(getDemoSession());
      },
      (err) => {
        setIsStreaming(false);
        // Remove the empty assistant message we added
        setMessages((prev) => prev.slice(0, -1));
        
        let message = 'An error occurred. Please try again.';
        if (err && err.error) {
          if (err.error.code === 'DEMO_QUOTA_EXCEEDED') {
            message = err.error.message || 'You have reached the demo limit.';
            if (session) {
              const updatedSession = { ...session, messageCount: 5 };
              localStorage.setItem('demo_session', JSON.stringify(updatedSession));
              setSession(updatedSession);
            }
          } else if (err.error.code === 'SERVICE_UNAVAILABLE') {
            message = err.error.message || 'AI service temporarily unavailable. Please try again shortly.';
          } else {
            message = err.error.message || message;
          }
        } else if (err && err.message) {
          message = err.message;
        }
        setErrorMsg(message);
      }
    );
  };

  const isQuotaExceeded = (session ? session.messageCount >= 5 : false) || errorMsg?.includes('reached the demo limit');

  return (
    <section id="live-demo" className="py-20 relative bg-slate-950 text-white overflow-hidden">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[300px] h-[300px] bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl mx-auto px-4 relative z-10">
        <div className="text-center mb-10">
          <span className="px-3 py-1 inline-flex items-center gap-1.5 text-xs font-semibold tracking-wider uppercase text-indigo-400 bg-indigo-400/10 border border-indigo-400/20 rounded-full mb-3">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" /> Dogfooding Demo
          </span>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Try the Live Demo
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-xl mx-auto">
            Interact with our assistant in real time. Experience the streaming speed and response quality firsthand.
          </p>
        </div>

        {/* Premium Glassmorphic Card */}
        <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[500px]">
          {/* Header */}
          <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-3 h-3 bg-emerald-500 rounded-full" />
                <div className="absolute inset-0 w-3 h-3 bg-emerald-500 rounded-full animate-ping opacity-75" />
              </div>
              <div>
                <span className="font-semibold text-sm">Demo Assistant</span>
                <p className="text-[10px] text-slate-500 leading-none mt-0.5">Powered by RAG Engine</p>
              </div>
            </div>
            {session && (
              <span 
                data-testid="demo-counter"
                className="text-xs font-mono px-2.5 py-1 bg-slate-800/80 border border-slate-700/50 rounded-md text-slate-400"
              >
                {Math.min(session.messageCount, 5)} / 5 messages
              </span>
            )}
          </div>

          {/* Messages List */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 max-w-[85%] ${
                  msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/15 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                  </div>
                )}
                <div>
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-none'
                        : 'bg-slate-800/60 border border-slate-800 text-slate-100 rounded-tl-none'
                    }`}
                  >
                    {msg.content || (
                      <span className="flex items-center gap-1 py-1">
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Fallback Errors */}
          {errorMsg && !isQuotaExceeded && (
            <div className="mx-6 mb-4 p-3 bg-red-950/40 border border-red-500/30 text-red-200 text-xs rounded-xl flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Quota Exceeded Block */}
          {isQuotaExceeded && (
            <div className="mx-6 mb-4 p-5 bg-indigo-950/20 border border-indigo-500/20 text-center rounded-xl animate-fade-in">
              <p className="text-sm text-indigo-200 mb-3">
                You have reached the demo limit. Start your free trial to continue.
              </p>
              <a
                href="/register?source=demo"
                data-testid="demo-cta-trial"
                className="inline-flex items-center justify-center px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition-colors shadow-lg shadow-indigo-600/20"
              >
                Start Your Free Trial
              </a>
            </div>
          )}

          {/* Form Input */}
          <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900/40 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isQuotaExceeded ? "Demo limit reached" : "Ask about our features, security, plans..."}
              disabled={isQuotaExceeded || isStreaming}
              data-testid="demo-chat-input"
              className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30 rounded-xl text-sm placeholder-slate-500 outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={isQuotaExceeded || isStreaming || !input.trim()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl flex items-center justify-center transition-colors disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
