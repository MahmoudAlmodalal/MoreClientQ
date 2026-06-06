'use client';

import React from 'react';
import { FileUp, Sliders, Code } from 'lucide-react';

interface Step {
  number: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}

export default function HowItWorks() {
  const steps: Step[] = [
    {
      number: '01',
      icon: <FileUp className="w-6 h-6 text-indigo-400" />,
      title: 'Connect your Knowledge Base',
      description: 'Upload PDF files, text documents, or link web URLs. Our system automatically parses, chunks, and stores them securely in vector databases.'
    },
    {
      number: '02',
      icon: <Sliders className="w-6 h-6 text-indigo-400" />,
      title: 'Customize Prompt & Style',
      description: 'Define the assistant system instructions, adjust response temperature, name the bot, and customize widget branding colors to match your app.'
    },
    {
      number: '03',
      icon: <Code className="w-6 h-6 text-indigo-400" />,
      title: 'Embed JavaScript Widget',
      description: 'Copy our single-line JS snippet or iframe code, paste it into your html/application layout, and start chatting with visitors instantly.'
    }
  ];

  return (
    <section id="how-it-works" className="py-24 bg-slate-950 text-white relative border-t border-slate-900/60">
      <div className="max-w-6xl mx-auto px-4 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Get set up in three simple steps
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-xl mx-auto">
            Our platform removes the complexity of building custom AI support agents. You provide the files, we handle the infrastructure.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 relative">
          {/* Connector Line (visible only on desktop) */}
          <div className="hidden lg:block absolute top-[56px] left-[15%] right-[15%] h-[1px] bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-indigo-500/20 z-0" />

          {steps.map((step, idx) => (
            <div key={idx} className="relative z-10 flex flex-col items-center text-center px-4">
              {/* Step Icon & Number */}
              <div className="relative mb-6">
                <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center relative shadow-xl">
                  {step.icon}
                </div>
                <span className="absolute -top-2 -right-2 w-7 h-7 bg-indigo-600 rounded-full border-2 border-slate-950 flex items-center justify-center text-[10px] font-bold font-mono">
                  {step.number}
                </span>
              </div>

              {/* Text info */}
              <h3 className="text-lg font-bold mb-3 text-slate-100">{step.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed max-w-xs">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
