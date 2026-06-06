'use client';

import React from 'react';

export default function LogoStrip() {
  const partners = [
    { name: 'Stripe', logo: 'Stripe' },
    { name: 'Vercel', logo: 'Vercel' },
    { name: 'Supabase', logo: 'Supabase' },
    { name: 'OpenAI', logo: 'OpenAI' },
    { name: 'GitHub', logo: 'GitHub' },
    { name: 'Slack', logo: 'Slack' }
  ];

  return (
    <section className="py-12 bg-slate-950 border-y border-slate-900 overflow-hidden">
      <div className="max-w-6xl mx-auto px-4">
        <p className="text-center text-xs font-semibold uppercase tracking-wider text-slate-500 mb-8">
          Trusted by engineers at modern startups and SMBs
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 md:gap-x-16 opacity-60">
          {partners.map((partner, index) => (
            <div
              key={index}
              className="text-slate-400 font-mono text-sm md:text-base font-bold tracking-tight hover:text-white transition-colors cursor-default"
            >
              {"//"}{partner.name.toUpperCase()}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
