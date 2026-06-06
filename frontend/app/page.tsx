"use client";

import * as React from "react";
import Link from "next/link";
import { getCookie, decodeJwt } from "@/lib/api";
import { Bot, ShieldCheck, Zap, Sparkles, LogIn, PlusCircle, ArrowRight, LayoutDashboard } from "lucide-react";

export default function Home() {
  const [tenantSlug, setTenantSlug] = React.useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = React.useState(false);
  const [userEmail, setUserEmail] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const hostname = window.location.hostname;
      const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || "localhost";
      
      // Resolve tenant slug (e.g. acme from acme.localhost)
      if (hostname !== rootDomain && hostname.endsWith(`.${rootDomain}`)) {
        const slug = hostname.slice(0, hostname.length - rootDomain.length - 1);
        if (slug && slug !== "www" && slug !== "api") {
          setTenantSlug(slug);
        }
      }

      // Check auth token
      const token = getCookie("access_token");
      if (token) {
        setIsLoggedIn(true);
        const claims = decodeJwt(token);
        if (claims && claims.sub) {
          // Decode email from JWT payload or default to authenticated state
          setUserEmail(claims.email || "Authenticated User");
        }
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans relative overflow-hidden flex flex-col justify-between selection:bg-indigo-500/30">
      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] rounded-full bg-purple-500/10 blur-[100px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 max-w-7xl mx-auto w-full px-6 py-5 flex items-center justify-between border-b border-indigo-500/10">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-md shadow-indigo-500/10">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Antigravity AI
          </span>
        </div>

        <div className="flex items-center gap-4">
          {isLoggedIn ? (
            <Link
              href="/dashboard"
              className="flex items-center gap-2 text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition duration-200"
            >
              <LayoutDashboard className="h-4 w-4" />
              Go to Dashboard
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="flex items-center gap-1 text-sm font-semibold hover:text-white text-slate-300 transition duration-200"
              >
                <LogIn className="h-4 w-4" />
                Sign In
              </Link>
              <Link
                href="/register"
                className="hidden sm:flex items-center gap-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition duration-200 shadow-md shadow-indigo-600/10"
              >
                <PlusCircle className="h-4 w-4" />
                New Workspace
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Content */}
      <main className="relative z-10 max-w-5xl mx-auto w-full px-6 py-16 flex flex-col items-center justify-center text-center my-auto">
        
        {/* Subdomain-specific Portal Alert */}
        {tenantSlug && (
          <div className="mb-8 p-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center gap-3 pr-4 animate-fade-in">
            <span className="bg-indigo-600 text-white font-extrabold uppercase text-[10px] tracking-wider px-2.5 py-1 rounded-full">
              Workspace Resolved
            </span>
            <span className="text-sm font-medium text-slate-300">
              Welcome to the <strong className="text-indigo-400 uppercase">{tenantSlug}</strong> tenant environment.
            </span>
          </div>
        )}

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight max-w-4xl bg-gradient-to-b from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
          Secure, Subdomain-Isolated <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-indigo-400 via-indigo-200 to-purple-400 bg-clip-text text-transparent">
            Multi-Tenant AI Workspaces
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl leading-relaxed">
          Create completely isolated workspaces for your team. Empower employees with customizable AI assistants supported by private vector-based document ingestion and Postgres Row-Level Security.
        </p>

        {/* Dynamic Action Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center w-full max-w-md">
          {tenantSlug ? (
            <>
              <Link
                href="/login"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 active:scale-[0.98] transition-all duration-200"
              >
                Sign In to {tenantSlug.toUpperCase()}
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/register"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 font-semibold px-6 py-3.5 rounded-xl transition duration-200"
              >
                Create Another Tenant
              </Link>
            </>
          ) : (
            <>
              <Link
                href="/register"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 active:scale-[0.98] transition-all duration-200"
              >
                Launch Custom Workspace
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 font-semibold px-8 py-3.5 rounded-xl transition duration-200"
              >
                Enter Existing Workspace
              </Link>
            </>
          )}
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 w-full text-left">
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-indigo-500/20 transition duration-300 flex flex-col gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-200 text-md">Row-Level Security (RLS)</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Every query executes with an active session tenant filter, ensuring tenant data is isolated strictly at the database engine level.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-indigo-500/20 transition duration-300 flex flex-col gap-3">
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Zap className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-200 text-md">Subdomain Routing</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Next.js Edge middleware intercepts requests, validates the subdomain slug via a Redis cache, and sets context in &lt; 15ms.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 hover:border-indigo-500/20 transition duration-300 flex flex-col gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-200 text-md">Custom Ingestion & AI</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Upload documents, ingest text vectors, and instantiate custom-engineered assistant parameters for fine-tuned context.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 max-w-7xl mx-auto w-full px-6 py-8 flex flex-col sm:flex-row items-center justify-between border-t border-indigo-500/10 text-slate-500 text-sm gap-4">
        <div>
          &copy; {new Date().getFullYear()} Antigravity AI Platform. All rights reserved.
        </div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-slate-300 transition duration-200">Documentation</a>
          <a href="#" className="hover:text-slate-300 transition duration-200">Security Model</a>
          <a href="#" className="hover:text-slate-300 transition duration-200">Github</a>
        </div>
      </footer>
    </div>
  );
}
