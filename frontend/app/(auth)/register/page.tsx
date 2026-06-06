"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { fetchApi, setCookie, decodeJwt } from "@/lib/api";
import { KeyRound, Mail, AlertCircle, Loader2, Globe, Building2, User } from "lucide-react";

export default function RegisterPage() {
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("token");

  // State for Tenant Registration
  const [slug, setSlug] = React.useState("");
  const [companyName, setCompanyName] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  
  // State for Invitation Acceptance
  const [invitePassword, setInvitePassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");

  // Common UI State
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState("");

  // Helper to handle auto login after registration
  const performAutoLogin = async (loginEmail: string, loginPass: string) => {
    try {
      const authData = await fetchApi("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: loginEmail, password: loginPass }),
      });

      // Save tokens in cookies
      setCookie("access_token", authData.access_token, 7);
      if (authData.refresh_token) {
        setCookie("refresh_token", authData.refresh_token, 7);
      }

      // Decode JWT to redirect to the correct subdomain
      const claims = decodeJwt(authData.access_token);
      const tenantSlugClaim = claims?.tenant_slug;

      if (tenantSlugClaim) {
        const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || "localhost";
        const port = window.location.port ? `:${window.location.port}` : "";
        const protocol = window.location.protocol;
        
        window.location.href = `${protocol}//${tenantSlugClaim}.${rootDomain}${port}/dashboard`;
      } else {
        window.location.href = "/dashboard";
      }
    } catch {
      // If auto login fails, redirect them to login page to login manually
      window.location.href = "/login";
    }
  };

  const handleRegisterTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    // Slug validation helper
    const slugRegex = /^[a-z0-9-]+$/;
    if (!slugRegex.test(slug)) {
      setError("Subdomain slug must contain only lowercase letters, numbers, and hyphens.");
      setIsLoading(false);
      return;
    }

    try {
      await fetchApi("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          slug: slug.toLowerCase(),
          tenant_name: companyName,
          owner_email: email,
          owner_password: password,
          owner_full_name: fullName,
        }),
      });

      setSuccess("Tenant workspace created successfully! Logging you in...");
      
      // Auto login
      await performAutoLogin(email, password);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to register tenant";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleAcceptInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (invitePassword !== confirmPassword) {
      setError("Passwords do not match");
      setIsLoading(false);
      return;
    }

    try {
      const data = await fetchApi("/auth/invite/accept", {
        method: "POST",
        body: JSON.stringify({
          token: inviteToken,
          password: invitePassword,
        }),
      });

      setSuccess("Account activated successfully! Logging you in...");

      // Auto login the accepted user
      await performAutoLogin(data.data.email, invitePassword);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to accept invitation. The link may have expired.";
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  if (inviteToken) {
    // RENDER: Invitation Acceptance Form
    return (
      <div className="space-y-6">
        <div className="space-y-2 text-center lg:text-left">
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Accept Invitation
          </h2>
          <p className="text-sm text-slate-400">
            Set your password to activate your account and join the workspace
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-400">
            <Loader2 className="h-5 w-5 shrink-0 animate-spin" />
            <p>{success}</p>
          </div>
        )}

        <form onSubmit={handleAcceptInvite} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="invitePassword">
              Choose Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <KeyRound className="h-5 w-5" />
              </span>
              <input
                id="invitePassword"
                type="password"
                required
                disabled={isLoading}
                value={invitePassword}
                onChange={(e) => setInvitePassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="confirmPassword">
              Confirm Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <KeyRound className="h-5 w-5" />
              </span>
              <input
                id="confirmPassword"
                type="password"
                required
                disabled={isLoading}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
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
                Activating...
              </>
            ) : (
              "Activate Account"
            )}
          </button>
        </form>
      </div>
    );
  }

  // RENDER: Tenant Registration Form
  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center lg:text-left">
        <h2 className="text-3xl font-bold tracking-tight text-white">
          Create a workspace
        </h2>
        <p className="text-sm text-slate-400">
          Build isolated, subdomain-mapped AI assistants in minutes
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-400">
          <Loader2 className="h-5 w-5 shrink-0 animate-spin" />
          <p>{success}</p>
        </div>
      )}

      <form onSubmit={handleRegisterTenant} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="companyName">
              Company Name
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Building2 className="h-5 w-5" />
              </span>
              <input
                id="companyName"
                type="text"
                required
                disabled={isLoading}
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Acme Corp"
                className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="slug">
              Subdomain Slug
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Globe className="h-5 w-5" />
              </span>
              <input
                id="slug"
                type="text"
                required
                disabled={isLoading}
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="acme"
                className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
              />
            </div>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="fullName">
            Owner Full Name
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
              <User className="h-5 w-5" />
            </span>
            <input
              id="fullName"
              type="text"
              required
              disabled={isLoading}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
            />
          </div>
        </div>

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
              placeholder="owner@company.com"
              className="w-full bg-slate-900 border border-slate-800 text-white rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
            />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider" htmlFor="password">
            Password
          </label>
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
              Registering workspace...
            </>
          ) : (
            "Create Workspace"
          )}
        </button>
      </form>

      <div className="text-center text-sm text-slate-500">
        Already have a workspace?{" "}
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold underline-offset-4 hover:underline">
          Log In
        </Link>
      </div>
    </div>
  );
}
