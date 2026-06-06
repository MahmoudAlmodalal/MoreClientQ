'use client';

import React from 'react';
import { Database, ShieldCheck, Zap, UserCheck, Code, BarChart3 } from 'lucide-react';

interface FeatureItem {
  icon: React.ReactNode;
  title: string;
  description: string;
}

export default function Features() {
  const features: FeatureItem[] = [
    {
      icon: <Database className="w-6 h-6 text-indigo-400" />,
      title: 'Custom Knowledge Bases (RAG)',
      description: 'Upload PDFs, Word docs, or text files to train your assistants in seconds. Our automated indexing prepares documents for instant querying.'
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-indigo-400" />,
      title: 'Multi-Tenant Security (RLS)',
      description: 'Strict logical isolation guarantees data privacy. Built with PostgreSQL Row-Level Security and tenant-isolated vector store separation.'
    },
    {
      icon: <Zap className="w-6 h-6 text-indigo-400" />,
      title: 'Real-Time Streaming (SSE)',
      description: 'Engage customers with instant, low-latency streaming responses using Server-Sent Events (SSE). No more waiting for full messages to load.'
    },
    {
      icon: <UserCheck className="w-6 h-6 text-indigo-400" />,
      title: 'Seamless Human Handoff',
      description: 'Transfer complex customer queries directly to human support agents. Keep a single continuous conversation history across AI and human phases.'
    },
    {
      icon: <Code className="w-6 h-6 text-indigo-400" />,
      title: 'Single-Line Embed JS',
      description: 'Integrate the live assistant widget on any web page by copying a single line of JavaScript or using our pre-built iframe embed code.'
    },
    {
      icon: <BarChart3 className="w-6 h-6 text-indigo-400" />,
      title: 'Granular Token & Usage Analytics',
      description: 'Monitor token expenditure, query logs, customer satisfaction scores, and active user analytics in real time across all assistants.'
    }
  ];

  return (
    <section id="features" className="py-24 bg-slate-950 text-white relative">
      <div className="max-w-6xl mx-auto px-4 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Engineered for growth and security
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-xl mx-auto">
            Everything you need to embed secure, customizable, and lightning-fast AI customer support into your applications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="p-8 rounded-2xl bg-slate-900/40 border border-slate-900 hover:border-slate-800 hover:bg-slate-900/60 transition-all group duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                {feature.icon}
              </div>
              <h3 className="text-lg font-bold mb-3 text-slate-100 group-hover:text-white transition-colors">
                {feature.title}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
