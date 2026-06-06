import React from 'react';
import { Metadata } from 'next';
import Hero from '../../components/landing/Hero';
import LogoStrip from '../../components/landing/LogoStrip';
import Features from '../../components/landing/Features';
import HowItWorks from '../../components/landing/HowItWorks';
import LiveDemo from '../../components/landing/LiveDemo';
import Pricing from '../../components/landing/Pricing';
import Testimonials from '../../components/landing/Testimonials';
import FooterCta from '../../components/landing/FooterCta';
import ScrollReveal from '../../components/landing/ScrollReveal';

export function generateMetadata(): Metadata {
  return {
    title: 'Antigravity AI - Multi-Tenant AI Assistant Platform',
    description: 'Deploy secure, isolated, and lightning-fast AI customer support assistants powered by custom RAG in minutes.',
    openGraph: {
      title: 'Antigravity AI - Multi-Tenant AI Assistant Platform',
      description: 'Deploy secure, isolated, and lightning-fast AI customer support assistants powered by custom RAG in minutes.',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Antigravity AI - Multi-Tenant AI Assistant Platform',
      description: 'Deploy secure, isolated, and lightning-fast AI customer support assistants powered by custom RAG in minutes.',
    },
  };
}

export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-slate-950 overflow-x-hidden">
      <Hero />
      <ScrollReveal>
        <LogoStrip />
      </ScrollReveal>
      <ScrollReveal>
        <Features />
      </ScrollReveal>
      <ScrollReveal>
        <HowItWorks />
      </ScrollReveal>
      <ScrollReveal>
        <LiveDemo />
      </ScrollReveal>
      <ScrollReveal>
        <Pricing />
      </ScrollReveal>
      <ScrollReveal>
        <Testimonials />
      </ScrollReveal>
      <ScrollReveal>
        <FooterCta />
      </ScrollReveal>
    </main>
  );
}
