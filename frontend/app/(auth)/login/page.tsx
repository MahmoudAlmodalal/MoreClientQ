"use client";

import * as React from "react";
import Link from "next/link";
import { fetchApi, setCookie, decodeJwt } from "@/lib/api";
import { KeyRound, Mail, AlertCircle, Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [tenantSlug, setTenantSlug] = React.useState<string | null>(null);

  React.useEffect(() => {
    // Determine tenant slug from hostname if on a subdomain
    if (typeof window !== "undefined") {
      const hostname = window.location.hostname;
      const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || "localhost";
      
      // If hostname is e.g. "acme.localhost", slug is "acme"
      if (hostname !== rootDomain && hostname.endsWith(`.${rootDomain}`)) {
        const slug = hostname.slice(0, hostname.length - rootDomain.length - 1);
        if (slug && slug !== "www" && slug !== "api") {
          setTenantSlug(slug);
        }
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const data = await fetchApi("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      // Save tokens in cookies
      setCookie("access_token", data.access_token, 7);
      if (data.refresh_token) {
        setCookie("refresh_token", data.refresh_token, 7);
      }

      // Decode JWT to find redirect destination
      const claims = decodeJwt(data.access_token);
      const slug = claims?.tenant_slug;

      if (slug) {
        const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || "localhost";
        const currentHostname = window.location.hostname;
        const port = window.location.port ? `:${window.location.port}` : "";
        const protocol = window.location.protocol;

        // If we are logging in from a different hostname (e.g. root platform), redirect to the subdomain
        if (currentHostname !== `${slug}.${rootDomain}`) {
          window.location.href = `${protocol}//${slug}.${rootDomain}${port}/dashboard`;
          return;
        }
      }
      
      // Already on the correct subdomain (or fallback) -> redirect to dashboard
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Invalid email or password";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center lg:text-left">
        <h2 className="text-3xl font-bold tracking-tight text-white">
          Welcome back
        </h2>
        <p className="text-sm text-slate-400">
          {tenantSlug ? (
            <span>
              Log in to your <strong className="text-indigo-400 uppercase">{tenantSlug}</strong> workspace
            </span>
          ) : (
            "Enter your credentials to log in to your tenant account"
          )}
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="email">
            Email Address
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
              <Mail className="h-5 w-5" />
            </span>
            <input
              id="email"
              type="email"
              required
              disabled={isLoading}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
            />
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="password">
              Password
            </label>
          </div>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
              <KeyRound className="h-5 w-5" />
            </span>
            <input
              id="password"
              type="password"
              required
              disabled={isLoading}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium py-3 rounded-lg shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/20 active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Logging in...
            </>
          ) : (
            "Log In"
          )}
        </button>
      </form>

      <div className="text-center text-sm text-slate-500">
        Don&apos;t have a workspace?{" "}
        <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-semibold underline-offset-4 hover:underline">
          Create platform tenant
        </Link>
      </div>
    </div>
  );
}
