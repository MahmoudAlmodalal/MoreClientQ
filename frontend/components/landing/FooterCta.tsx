'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function FooterCta() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email)) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }

    router.push(`/register?email=${encodeURIComponent(email)}&source=footer`);
  };

  return (
    <section className="py-24 relative bg-slate-950 text-white border-t border-slate-900 overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
        <span className="px-3 py-1 inline-flex items-center gap-1.5 text-xs font-semibold tracking-wider uppercase text-indigo-400 bg-indigo-400/10 border border-indigo-400/20 rounded-full mb-6">
          <Sparkles className="w-3.5 h-3.5" /> Start Building Today
        </span>
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
          Ready to scale your customer support?
        </h2>
        <p className="mt-6 text-lg text-slate-400 max-w-xl mx-auto">
          Get started with your custom AI assistants in minutes. No credit card required, 14-day free trial.
        </p>

        <form onSubmit={handleSubmit} className="mt-10 max-w-md mx-auto">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your work email"
                data-testid="footer-cta-email-input"
                className="w-full px-4 py-3 bg-slate-900 border border-slate-800 focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/30 rounded-xl text-sm placeholder-slate-500 outline-none transition-all"
              />
            </div>
            <button
              type="submit"
              data-testid="footer-cta-submit-btn"
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25"
            >
              Get Started <ArrowRight className="w-4 h-4" />
            </button>
          </div>
          {errorMsg && (
            <p
              data-testid="footer-cta-error"
              className="mt-3 text-sm text-red-400 text-left sm:text-center font-medium"
            >
              {errorMsg}
            </p>
          )}
        </form>
      </div>
    </section>
  );
}
