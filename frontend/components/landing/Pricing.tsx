'use client';

import React from 'react';
import Link from 'next/link';
import { Check, Sparkles } from 'lucide-react';

interface PricingTier {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  ctaText: string;
  ctaHref: string;
  testid: string;
  isPopular?: boolean;
}

export default function Pricing() {
  const tiers: PricingTier[] = [
    {
      name: 'Starter',
      price: '$0',
      period: 'forever',
      description: 'Ideal for getting started or small personal projects.',
      features: [
        '1 AI Assistant',
        '5 Documents limit',
        '50MB total storage',
        'Standard response speed',
        'Community support'
      ],
      ctaText: 'Start Free Trial',
      ctaHref: '/register?plan=starter',
      testid: 'pricing-cta-starter'
    },
    {
      name: 'Pro',
      price: '$49',
      period: 'month',
      description: 'Perfect for startups and growing businesses.',
      features: [
        '5 AI Assistants',
        '100 Documents limit',
        '1GB total storage',
        'Priority streaming speed',
        'Email & Chat support',
        'Remove platform branding'
      ],
      ctaText: 'Start Free Trial',
      ctaHref: '/register?plan=pro',
      testid: 'pricing-cta-pro',
      isPopular: true
    },
    {
      name: 'Business',
      price: '$199',
      period: 'month',
      description: 'Built for teams requiring robust operations.',
      features: [
        'Unlimited Assistants',
        'Unlimited Documents',
        'Unlimited storage space',
        'Fastest API throughput',
        '24/7 dedicated support',
        'SAML Single Sign-On (SSO)',
        'Custom domain widgets'
      ],
      ctaText: 'Start Free Trial',
      ctaHref: '/register?plan=business',
      testid: 'pricing-cta-business'
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'Custom configurations and dedicated SLAs for large scale.',
      features: [
        'Isolated Postgres database',
        'Dedicated server hosting',
        'HIPAA & SOC2 compliance packages',
        'Tailored RAG vector stores',
        'Custom integration engineering',
        'Dedicated account manager'
      ],
      ctaText: 'Contact Sales',
      ctaHref: '/contact',
      testid: 'pricing-cta-enterprise'
    }
  ];

  return (
    <section id="pricing" className="py-24 bg-slate-950 text-white relative">
      <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 relative z-10">
        <div className="text-center mb-16">
          <span className="px-3 py-1 inline-flex items-center gap-1.5 text-xs font-semibold tracking-wider uppercase text-indigo-400 bg-indigo-400/10 border border-indigo-400/20 rounded-full mb-3">
            Transparent Pricing
          </span>
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
            Choose the right plan for your business
          </h2>
          <p className="mt-4 text-lg text-slate-400 max-w-xl mx-auto">
            Scale seamlessly as your database grows. Try any plan free for 14 days. Cancel anytime.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {tiers.map((tier, idx) => (
            <div
              key={idx}
              className={`p-8 rounded-2xl bg-slate-900/40 border flex flex-col justify-between relative transition-all duration-300 ${
                tier.isPopular
                  ? 'border-indigo-500 bg-slate-900/60 ring-2 ring-indigo-500/20 md:scale-105 z-10'
                  : 'border-slate-900 hover:border-slate-800'
              }`}
            >
              {tier.isPopular && (
                <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-0.5 text-[10px] font-bold uppercase tracking-widest text-white bg-indigo-600 rounded-full flex items-center gap-1 shadow-md">
                  <Sparkles className="w-3 h-3" /> Most Popular
                </span>
              )}

              <div>
                <h3 className="text-xl font-bold text-slate-100">{tier.name}</h3>
                <p className="mt-2 text-xs text-slate-500 min-h-[32px]">{tier.description}</p>
                
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold tracking-tight">{tier.price}</span>
                  {tier.period && (
                    <span className="text-xs text-slate-500">/{tier.period}</span>
                  )}
                </div>

                <ul className="mt-8 space-y-4">
                  {tier.features.map((feature, fIdx) => (
                    <li key={fIdx} className="flex items-start gap-2.5 text-xs text-slate-400">
                      <Check className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-8">
                <Link
                  href={tier.ctaHref}
                  data-testid={tier.testid}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center transition-all ${
                    tier.isPopular
                      ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/50'
                  }`}
                >
                  {tier.ctaText}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
