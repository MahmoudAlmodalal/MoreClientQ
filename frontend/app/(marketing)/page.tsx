import React from 'react';
import Hero from '../../components/landing/Hero';
import LogoStrip from '../../components/landing/LogoStrip';
import Features from '../../components/landing/Features';
import HowItWorks from '../../components/landing/HowItWorks';
import LiveDemo from '../../components/landing/LiveDemo';
import FooterCta from '../../components/landing/FooterCta';

export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-slate-950">
      <Hero />
      <LogoStrip />
      <Features />
      <HowItWorks />
      <LiveDemo />
      <FooterCta />
    </main>
  );
}
