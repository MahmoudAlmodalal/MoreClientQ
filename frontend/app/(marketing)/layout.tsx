import React from 'react';

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#030712] text-[#F9FAFB] selection:bg-[#6366F1] selection:text-white overflow-x-hidden">
      {/* Sticky Header Shell */}
      <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#030712]/80 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-6 w-6 rounded-md bg-gradient-to-tr from-indigo-500 to-violet-500" />
            <span className="font-semibold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-[#D1D5DB]">
              Antigravity AI
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm text-[#9CA3AF]">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="https://docs.example.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Docs</a>
          </nav>
          <div className="flex items-center gap-4">
            <a href="/login" className="text-sm font-medium hover:text-white transition-colors">Log in</a>
            <a href="/register" className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-all">
              Start Free Trial
            </a>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full">
        {children}
      </main>

      {/* Footer Shell */}
      <footer className="w-full border-t border-white/[0.08] bg-[#030712] py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <span className="h-5 w-5 rounded bg-gradient-to-tr from-indigo-500 to-violet-500" />
            <span className="font-semibold text-sm tracking-tight text-white">
              Antigravity AI
            </span>
          </div>
          <p className="text-xs text-[#6B7280]">
            &copy; {new Date().getFullYear()} Antigravity AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
