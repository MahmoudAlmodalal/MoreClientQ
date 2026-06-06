'use client';

import React from 'react';
import Link from 'next/link';
import { Bot, Github, Twitter, MessageSquare } from 'lucide-react';

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
            <Link href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors">
              <Github className="w-4 h-4" />
            </Link>
            <Link href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors">
              <Twitter className="w-4 h-4" />
            </Link>
            <Link href="https://slack.com" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors">
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
