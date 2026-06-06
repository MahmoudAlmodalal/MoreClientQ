'use client';

import React from 'react';
import { Star } from 'lucide-react';

interface Testimonial {
  quote: string;
  name: string;
  role: string;
  company: string;
  avatarUrl?: string;
}

export default function Testimonials() {
  const testimonials: Testimonial[] = [
    {
      quote: "Integrating our PDF user manuals took less than five minutes. Our users now get immediate answers, which has cut support tickets by 40%. The RLS isolation is what convinced our compliance team.",
      name: "Sarah Jenkins",
      role: "VP of Product",
      company: "CloudFlow"
    },
    {
      quote: "As an SMB, we couldn't afford a full-time 24/7 support team. This AI assistant platform lets us resolve user queries overnight. The real-time streaming is incredibly fast and feels very natural.",
      name: "Marcus Thorne",
      role: "Founder & CEO",
      company: "GrowthKit"
    },
    {
      quote: "We needed a support assistant that we could embed on multiple platforms while maintaining strict client data privacy. The multi-tenant security architecture is robust and holds up to audits.",
      name: "Elena Rostova",
      role: "Security Engineer",
      company: "DataVault"
    }
  ];

  return (
    <section id="testimonials" className="py-24 bg-slate-950 text-white border-t border-slate-900/60 relative">
      <div className="max-w-6xl mx-auto px-4 relative z-10">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Loved by product and support teams
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-xl mx-auto">
            See how startups and SMB owners are using our platform to automate customer support securely.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, idx) => (
            <div
              key={idx}
              className="p-8 rounded-2xl bg-slate-900/40 border border-slate-900 hover:border-slate-800 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex gap-1 mb-6">
                  {[...Array(5)].map((_, starIdx) => (
                    <Star key={starIdx} className="w-4 h-4 fill-indigo-400 text-indigo-400" />
                  ))}
                </div>
                <p className="text-sm text-slate-300 italic leading-relaxed">
                  &ldquo;{t.quote}&rdquo;
                </p>
              </div>

              <div className="mt-8 flex items-center gap-3 border-t border-slate-800/65 pt-6">
                {/* Visual initial avatar placeholder */}
                <div className="w-10 h-10 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-sm text-indigo-400">
                  {t.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">{t.name}</h4>
                  <p className="text-xs text-slate-500">{t.role}, {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
