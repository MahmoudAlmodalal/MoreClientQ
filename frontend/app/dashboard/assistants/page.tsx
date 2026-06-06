"use client";

import * as React from "react";
import { Plus, ArrowLeft, Bot, Sparkles, AlertCircle, Copy, Check, ShieldCheck, HelpCircle, User } from "lucide-react";
import Link from "next/link";
import { fetchApi, getCookie, decodeJwt } from "@/lib/api";
import { Button } from "@/components/ui/button";
import AssistantCard from "@/components/assistants/assistant-card";
import AssistantForm, { AssistantData } from "@/components/assistants/assistant-form";

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
  const [embedSnippet, setEmbedSnippet] = React.useState<string>("");
  const [isLoadingEmbed, setIsLoadingEmbed] = React.useState(false);
  const [isCopied, setIsCopied] = React.useState(false);

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

  const handleShowEmbedCode = async (assistant: AssistantData) => {
    if (!assistant.id) return;
    setEmbedAssistant(assistant);
    setIsLoadingEmbed(true);
    setIsCopied(false);
    try {
      const data = await fetchApi(`/assistants/${assistant.id}/embed`);
      setEmbedSnippet(data.snippet);
    } catch (err: unknown) {
      setEmbedSnippet("Failed to retrieve embed code: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setIsLoadingEmbed(false);
    }
  };

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(embedSnippet);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400">
                  <Sparkles className="h-5 w-5" />
                </div>
                <h2 className="text-xl font-bold text-white tracking-tight">Widget Embed Snippet</h2>
              </div>
              <button
                onClick={() => setEmbedAssistant(null)}
                className="text-slate-400 hover:text-white transition duration-200 rounded-lg p-1 hover:bg-slate-800"
              >
                <Plus className="h-5 w-5 rotate-45" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-slate-400 text-xs leading-relaxed">
                Add this copy-pasteable script tag to the HTML body of your website or application. This will render the chat widget bubble automatically.
              </p>

              {isLoadingEmbed ? (
                <div className="h-32 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-center">
                  <div className="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <div className="relative group">
                  <pre className="bg-slate-950 border border-slate-850 p-4 rounded-xl text-indigo-300 text-xs overflow-x-auto font-mono max-w-full">
                    {embedSnippet}
                  </pre>
                  <button
                    onClick={handleCopySnippet}
                    className="absolute right-3 top-3 p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition hover:bg-slate-800 flex items-center gap-1 text-[10px] font-bold uppercase"
                  >
                    {isCopied ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              <div className="p-3.5 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-slate-400 text-[11px] flex gap-2">
                <HelpCircle className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
                <span>
                  The widget loads and executes client side. RLS access control ensures it can only access data vectors configured for the <strong>{embedAssistant.name}</strong> bot.
                </span>
              </div>
            </div>

            <div className="p-6 border-t border-slate-800 flex items-center justify-end bg-slate-950/40">
              <Button
                onClick={() => setEmbedAssistant(null)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
              >
                Close Dialog
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-900/20 border-t border-indigo-500/10 text-slate-500 text-xs py-4 text-center mt-auto">
        Antigravity AI Platform Sandbox &copy; {new Date().getFullYear()} — Multi-Tenant Row-Level Security active.
      </footer>
    </div>
  );
}
