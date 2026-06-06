'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Bot, Menu, X } from 'lucide-react';

export default function Nav() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-900/60 text-white">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" data-testid="nav-logo" className="flex items-center gap-2.5 font-bold tracking-tight text-slate-100 hover:text-white transition-colors">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-600/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <span className="text-sm md:text-base">Antigravity AI</span>
        </Link>

        {/* Desktop Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <Link href="#features" data-testid="nav-link-features" className="hover:text-slate-200 transition-colors">
            Features
          </Link>
          <Link href="#pricing" data-testid="nav-link-pricing" className="hover:text-slate-200 transition-colors">
            Pricing
          </Link>
          <Link href="https://docs.example.com" data-testid="nav-link-docs" target="_blank" rel="noopener noreferrer" className="hover:text-slate-200 transition-colors">
            Docs
          </Link>
        </nav>

        {/* Auth CTAs */}
        <div className="hidden md:flex items-center gap-4">
          <Link href="/login" data-testid="nav-link-login" className="text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors">
            Log In
          </Link>
          <Link
            href="/register"
            data-testid="nav-cta-register"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition-colors shadow-md shadow-indigo-600/10"
          >
            Get Started
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden p-1.5 hover:bg-slate-900 rounded-lg text-slate-400 hover:text-slate-200 transition-colors"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {isOpen && (
        <div className="md:hidden border-t border-slate-900 bg-slate-950 p-4 space-y-4 text-sm font-medium text-slate-400">
          <Link
            href="#features"
            onClick={() => setIsOpen(false)}
            className="block py-2 hover:text-slate-200"
          >
            Features
          </Link>
          <Link
            href="#pricing"
            onClick={() => setIsOpen(false)}
            className="block py-2 hover:text-slate-200"
          >
            Pricing
          </Link>
          <Link
            href="https://docs.example.com"
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setIsOpen(false)}
            className="block py-2 hover:text-slate-200"
          >
            Docs
          </Link>
          <div className="border-t border-slate-900 pt-4 flex flex-col gap-3">
            <Link
              href="/login"
              onClick={() => setIsOpen(false)}
              className="py-2 hover:text-slate-200"
            >
              Log In
            </Link>
            <Link
              href="/register"
              onClick={() => setIsOpen(false)}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-center shadow-md shadow-indigo-600/10"
            >
              Get Started
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
