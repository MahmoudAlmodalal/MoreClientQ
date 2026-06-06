'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowRight, Bot, Shield, User } from 'lucide-react';

interface MockMessage {
  role: 'user' | 'assistant';
  content: string;
}

const MOCK_CONVERSATION: MockMessage[] = [
  { role: 'user', content: 'Do you offer custom security configurations?' },
  { role: 'assistant', content: 'Yes! Our platform provides tenant isolation via Row-Level Security (RLS), isolated schema options, and custom vector store keys.' },
  { role: 'user', content: 'How fast can I integrate RAG on my site?' },
  { role: 'assistant', content: 'In under 5 minutes. Just upload your files (PDF, DOCX) and paste our single-line iframe/JS embed code.' }
];

export default function Hero() {
  const [messages, setMessages] = useState<MockMessage[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [typingText, setTypingText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    let active = true;
    
    const runSimulation = async () => {
      // Loop the mock conversation
      while (active) {
        setMessages([]);
        setCurrentIdx(0);
        await sleep(1000);

        for (let i = 0; i < MOCK_CONVERSATION.length; i++) {
          if (!active) return;
          const nextMsg = MOCK_CONVERSATION[i];

          if (nextMsg.role === 'user') {
            setIsTyping(true);
            setTypingText('');
            // Typewriter effect for user message
            for (let charIdx = 0; charIdx <= nextMsg.content.length; charIdx++) {
              if (!active) return;
              setTypingText(nextMsg.content.slice(0, charIdx));
              await sleep(40);
            }
            await sleep(400);
            setIsTyping(false);
            setMessages((prev) => [...prev, nextMsg]);
          } else {
            // Assistant response appears with a small delay
            setIsTyping(true);
            await sleep(600);
            setIsTyping(false);
            setMessages((prev) => [...prev, nextMsg]);
          }
          await sleep(2000);
        }
        await sleep(3000); // Pause before restarting loop
      }
    };

    runSimulation();

    return () => {
      active = false;
    };
  }, []);

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  return (
    <section className="relative pt-32 pb-24 md:pt-40 md:pb-32 bg-slate-950 text-white overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-10 right-1/4 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
        {/* Left: Text & CTAs */}
        <div className="lg:col-span-7 text-center lg:text-left space-y-8">
          <span className="px-3.5 py-1 inline-flex items-center gap-1.5 text-xs font-semibold tracking-wider uppercase text-indigo-400 bg-indigo-400/10 border border-indigo-400/20 rounded-full">
            <Bot className="w-3.5 h-3.5" /> Next-Gen AI Assistant Platform
          </span>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-[1.1] bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Deploy secure AI assistants for your customers.
          </h1>
          <p className="text-lg md:text-xl text-slate-400 max-w-xl mx-auto lg:mx-0">
            Empower your team and engage users with intelligent customer support bots. Upload documents, connect knowledge bases, and integrate widgets in minutes.
          </p>

          <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-4">
            <Link
              href="/register"
              data-testid="hero-primary-cta"
              className="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30"
            >
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="#pricing"
              data-testid="hero-secondary-cta"
              className="px-8 py-3.5 bg-slate-900 hover:bg-slate-800 active:bg-slate-950 text-slate-200 border border-slate-800 text-sm font-semibold rounded-xl transition-colors flex items-center justify-center"
            >
              View Pricing
            </Link>
          </div>
        </div>

        {/* Right: Mock Chat Animation */}
        <div className="lg:col-span-5 w-full max-w-md mx-auto">
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[380px] w-full">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/90 flex items-center gap-2">
              <div className="w-2.5 h-2.5 bg-red-500/80 rounded-full" />
              <div className="w-2.5 h-2.5 bg-yellow-500/80 rounded-full" />
              <div className="w-2.5 h-2.5 bg-green-500/80 rounded-full" />
              <span className="text-xs text-slate-500 font-mono ml-2">preview-assistant.js</span>
            </div>

            {/* Chat Box Area */}
            <div className="flex-1 p-5 overflow-y-auto space-y-4 font-sans text-xs">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-2.5 max-w-[85%] ${
                    msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.role === 'user' ? 'bg-indigo-600' : 'bg-slate-800 border border-slate-700'
                  }`}>
                    {msg.role === 'user' ? <User className="w-3 h-3 text-white" /> : <Bot className="w-3 h-3 text-indigo-400" />}
                  </div>
                  <div
                    className={`px-3 py-2 rounded-xl leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-none'
                        : 'bg-slate-800/80 border border-slate-800 text-slate-100 rounded-tl-none'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              
              {/* Typewriter message */}
              {isTyping && typingText && (
                <div className="flex gap-2.5 max-w-[85%] ml-auto flex-row-reverse">
                  <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0">
                    <User className="w-3 h-3 text-white" />
                  </div>
                  <div className="px-3 py-2 rounded-xl bg-indigo-600 text-white rounded-tr-none leading-relaxed">
                    {typingText}
                    <span className="animate-pulse font-mono">|</span>
                  </div>
                </div>
              )}

              {/* Bot thinking dots */}
              {isTyping && !typingText && (
                <div className="flex gap-2.5 max-w-[85%] mr-auto">
                  <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3 h-3 text-indigo-400" />
                  </div>
                  <div className="px-3 py-2 rounded-xl bg-slate-800/80 border border-slate-800 text-slate-100 rounded-tl-none flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
