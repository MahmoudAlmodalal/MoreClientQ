'use client';

import React from 'react';
import Link from 'next/link';
import { Bot, MessageSquare } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-950 text-slate-500 text-xs border-t border-slate-900/60 py-12">
      <div className="max-w-6xl mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Brand Column */}
        <div className="space-y-4">
          <Link href="/" className="flex items-center gap-2 font-bold text-slate-300 hover:text-white transition-colors">
            <Bot className="w-5 h-5 text-indigo-500" />
            <span>Antigravity AI</span>
          </Link>
          <p className="text-[11px] leading-relaxed text-slate-600">
            Deploy secure, scalable, and isolated custom AI chat assistants for startup founders and SMB owners.
          </p>
          <div className="flex gap-4 text-slate-600">
            <Link href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors" aria-label="GitHub">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
                <path d="M9 18c-4.51 2-5-2-7-2" />
              </svg>
            </Link>
            <Link href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors" aria-label="Twitter">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
              </svg>
            </Link>
            <Link href="https://slack.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors" aria-label="Slack">
              <MessageSquare className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Product Column */}
        <div>
          <h4 className="font-semibold text-slate-400 mb-4 uppercase tracking-wider text-[10px]">Product</h4>
          <ul className="space-y-2.5">
            <li>
              <Link href="#features" className="hover:text-slate-300 transition-colors">Features</Link>
            </li>
            <li>
              <Link href="#pricing" className="hover:text-slate-300 transition-colors">Pricing</Link>
            </li>
            <li>
              <Link href="#live-demo" className="hover:text-slate-300 transition-colors">Live Demo</Link>
            </li>
          </ul>
        </div>

        {/* Resources Column */}
        <div>
          <h4 className="font-semibold text-slate-400 mb-4 uppercase tracking-wider text-[10px]">Resources</h4>
          <ul className="space-y-2.5">
            <li>
              <Link href="https://docs.example.com" data-testid="footer-link-docs" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors">Docs</Link>
            </li>
            <li>
              <Link href="/quickstart" className="hover:text-slate-300 transition-colors">Quickstart</Link>
            </li>
            <li>
              <Link href="/help" className="hover:text-slate-300 transition-colors">Help Center</Link>
            </li>
          </ul>
        </div>

        {/* Legal Column */}
        <div>
          <h4 className="font-semibold text-slate-400 mb-4 uppercase tracking-wider text-[10px]">Legal</h4>
          <ul className="space-y-2.5">
            <li>
              <Link href="/privacy" data-testid="footer-link-privacy" className="hover:text-slate-300 transition-colors">Privacy Policy</Link>
            </li>
            <li>
              <Link href="/terms" className="hover:text-slate-300 transition-colors">Terms of Service</Link>
            </li>
            <li>
              <Link href="/security" className="hover:text-slate-300 transition-colors">Security Isolation</Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 mt-12 pt-8 border-t border-slate-900/60 flex flex-col sm:flex-row justify-between items-center gap-4 text-[11px] text-slate-600">
        <p>&copy; {currentYear} Antigravity AI Inc. All rights reserved.</p>
        <p>Built with Row-Level Security isolation guidelines.</p>
      </div>
    </footer>
  );
}
