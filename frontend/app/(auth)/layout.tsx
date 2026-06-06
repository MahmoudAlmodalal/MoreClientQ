import * as React from "react";
import Link from "next/link";
import { Sparkles, Bot, ShieldCheck, Zap } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-12 font-sans bg-slate-950 text-slate-100 selection:bg-indigo-500/30">
      {/* Brand & Marketing Column (Hidden on mobile) */}
      <div className="relative hidden flex-col justify-between p-10 lg:col-span-5 lg:flex bg-gradient-to-br from-indigo-950 via-slate-950 to-purple-950 border-r border-indigo-500/10 overflow-hidden">
        {/* Subtle glowing orbs */}
        <div className="absolute top-1/4 -left-20 w-80 h-80 rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="absolute bottom-1/4 -right-20 w-80 h-80 rounded-full bg-purple-500/10 blur-[100px]" />

        <div className="relative z-10 flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/20">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <Link href="/" className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Antigravity AI
          </Link>
        </div>

        <div className="relative z-10 my-auto space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight leading-tight text-white">
            Supercharge your team with isolated AI assistants
          </h1>
          <p className="text-lg text-slate-400">
            Secure, subdomain-isolated multi-tenant workspace with database row-level security and custom document ingestion.
          </p>

          <div className="space-y-4 pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">Strict Row-Level Database Isolation</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400">
                <Zap className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">Subdomain Resolved Redis Cache &lt; 15ms</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">Custom Knowledge Bases and Real-Time Chat</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-sm text-slate-500">
          &copy; {new Date().getFullYear()} Antigravity AI Inc. All rights reserved.
        </div>
      </div>

      {/* Main Content Column */}
      <div className="flex items-center justify-center p-6 sm:p-10 lg:col-span-7 bg-slate-950 relative">
        <div className="absolute top-10 right-10 z-20 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <span className="text-md font-bold text-white">Antigravity AI</span>
          </div>
        </div>
        <div className="w-full max-w-md space-y-8">
          {children}
        </div>
      </div>
    </div>
  );
}
