"use client";

import * as React from "react";
import { Plus, ArrowLeft, Bot, AlertCircle, ShieldCheck, User } from "lucide-react";
import Link from "next/link";
import { fetchApi, getCookie, decodeJwt } from "@/lib/api";
import { Button } from "@/components/ui/button";
import AssistantCard from "@/components/assistants/assistant-card";
import AssistantForm, { AssistantData } from "@/components/assistants/assistant-form";
import EmbedCodeModal from "@/components/assistants/embed-code-modal";

export default function AssistantsDashboardPage() {
  const [assistants, setAssistants] = React.useState<AssistantData[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [tenantSlug, setTenantSlug] = React.useState<string>("unknown");
  const [userEmail, setUserEmail] = React.useState<string>("user@company.com");
  const [userRole, setUserRole] = React.useState<string>("member");
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean>(false);

  // Form Modals State
  const [isFormOpen, setIsFormOpen] = React.useState(false);
  const [selectedAssistant, setSelectedAssistant] = React.useState<AssistantData | undefined>(undefined);

  // Embed Modal State
  const [embedAssistant, setEmbedAssistant] = React.useState<AssistantData | null>(null);

  // Page level errors
  const [error, setError] = React.useState<string | null>(null);
  const canManageAssistants = userRole === "owner" || userRole === "admin";

  const fetchAssistantsList = async () => {
    try {
      const data = await fetchApi("/assistants");
      setAssistants(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load assistants.");
    }
  };

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      // Determine tenant slug
      const hostname = window.location.hostname;
      const rootDomain = process.env.NEXT_PUBLIC_ROOT_DOMAIN || "localhost";
      if (hostname !== rootDomain && hostname.endsWith(`.${rootDomain}`)) {
        const slug = hostname.slice(0, hostname.length - rootDomain.length - 1);
        if (slug) setTenantSlug(slug);
      } else {
        setTenantSlug("demo");
      }

      // Check auth state
      const token = getCookie("access_token");
      if (token) {
        const claims = decodeJwt(token);
        if (claims) {
          setIsAuthenticated(true);
          setUserEmail(claims.email || "user@company.com");
          setUserRole(claims.role || "member");
        }
      }
    }

    const init = async () => {
      setIsLoading(true);
      await fetchAssistantsList();
      setIsLoading(false);
    };
    init();
  }, []);

  const handleCreateOrUpdate = async (formData: AssistantData) => {
    if (selectedAssistant?.id) {
      // Update
      const updated = await fetchApi(`/assistants/${selectedAssistant.id}`, {
        method: "PATCH",
        body: JSON.stringify(formData),
      });
      setAssistants((prev) =>
        prev.map((ast) => (ast.id === updated.id ? updated : ast))
      );
    } else {
      // Create
      const created = await fetchApi("/assistants", {
        method: "POST",
        body: JSON.stringify(formData),
      });
      setAssistants((prev) => [...prev, created]);
    }
    setIsFormOpen(false);
    setSelectedAssistant(undefined);
  };

  const handleDeleteAssistant = async (id: string) => {
    await fetchApi(`/assistants/${id}`, {
      method: "DELETE",
    });
    setAssistants((prev) => prev.filter((ast) => ast.id !== id));
  };

  const handleShowEmbedCode = (assistant: AssistantData) => {
    setEmbedAssistant(assistant);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Loading workspace custom agents...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans p-6">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-6 shadow-xl">
          <div className="h-14 w-14 rounded-full bg-red-500/10 text-red-400 flex items-center justify-center mx-auto border border-red-500/20">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Access Denied</h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              No authenticated session resolved for the <strong className="text-indigo-400 uppercase">{tenantSlug}</strong> workspace environment. Please sign in to manage assistants.
            </p>
          </div>
          <Link
            href="/login"
            className="w-full flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl transition duration-200"
          >
            Log In to Workspace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-indigo-500/30">
      
      {/* Header */}
      <header className="bg-slate-900/40 border-b border-indigo-500/10 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition hover:border-slate-700"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <span className="text-sm font-semibold tracking-tight text-white block leading-none">
                  Custom AI Assistants
                </span>
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mt-1 block">
                  {tenantSlug} Workspace
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              <User className="h-4 w-4 text-slate-400" />
              <div className="text-left text-xs leading-none">
                <span className="text-slate-300 font-medium block">{userEmail}</span>
                <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mt-0.5 block">{userRole}</span>
              </div>
            </div>
            {canManageAssistants && (
              <Button
                onClick={() => {
                  setSelectedAssistant(undefined);
                  setIsFormOpen(true);
                }}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center gap-1.5 shadow-lg shadow-indigo-600/20 px-4 py-2"
              >
                <Plus className="h-4.5 w-4.5" />
                <span>Create Assistant</span>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Grid Content */}
      <main className="max-w-7xl mx-auto w-full px-6 py-8 flex-1">
        
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-2.5">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Dashboard Title Section */}
        <div className="mb-8 space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Configure Workspace AI
          </h1>
          <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
            Create custom chatbots and agents tailored to your business knowledge base. Customize behavior, constraints, and system prompts with strict RLS multi-tenant data boundary isolation.
          </p>
        </div>

        {/* Empty state or list */}
        {assistants.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/20 border border-slate-800 max-w-md mx-auto space-y-6 mt-10">
            <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
              <Bot className="h-8 w-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-white">No AI Assistants Found</h3>
              <p className="text-slate-400 text-xs leading-relaxed">
                You haven&apos;t created any custom AI agents yet. Set up your first assistant to begin querying custom knowledge bases.
              </p>
            </div>
            {canManageAssistants && (
              <Button
                onClick={() => {
                  setSelectedAssistant(undefined);
                  setIsFormOpen(true);
                }}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
              >
                Configure First Assistant
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {assistants.map((ast) => (
              <AssistantCard
                key={ast.id}
                assistant={ast}
                canManage={canManageAssistants}
                onEdit={(assistant) => {
                  setSelectedAssistant(assistant);
                  setIsFormOpen(true);
                }}
                onDelete={handleDeleteAssistant}
                onShowEmbed={handleShowEmbedCode}
              />
            ))}
          </div>
        )}
      </main>

      {/* Form Dialog Modal */}
      {isFormOpen && canManageAssistants && (
        <AssistantForm
          title={selectedAssistant ? "Edit Assistant Settings" : "Configure New AI Assistant"}
          initialData={selectedAssistant}
          onSubmit={handleCreateOrUpdate}
          onClose={() => {
            setIsFormOpen(false);
            setSelectedAssistant(undefined);
          }}
        />
      )}

      {/* Embed Code modal */}
      {embedAssistant && (
        <EmbedCodeModal
          assistant={embedAssistant}
          onClose={() => setEmbedAssistant(null)}
        />
      )}

      {/* Footer */}
      <footer className="bg-slate-900/20 border-t border-indigo-500/10 text-slate-500 text-xs py-4 text-center mt-auto">
        Antigravity AI Platform Sandbox &copy; {new Date().getFullYear()} — Multi-Tenant Row-Level Security active.
      </footer>
    </div>
  );
}
