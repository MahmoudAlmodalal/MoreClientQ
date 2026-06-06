"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Database, Bot, Sparkles, AlertCircle, FileText, Globe } from "lucide-react";
import { fetchApi, getCookie, decodeJwt } from "@/lib/api";
import { Button } from "@/components/ui/button";
import FileUpload from "@/components/knowledge-base/file-upload";
import UrlIngestForm from "@/components/knowledge-base/url-ingest-form";
import DocumentList, { DocumentData } from "@/components/knowledge-base/document-list";

export default function KnowledgeBasePage() {
  const params = useParams();
  const router = useRouter();
  const assistantId = params.id as string;

  const [assistantName, setAssistantName] = React.useState<string>("Assistant");
  const [documents, setDocuments] = React.useState<DocumentData[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [userRole, setUserRole] = React.useState("member");
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [activeTab, setActiveTab] = React.useState<"file" | "url">("file");

  const canManage = userRole === "owner" || userRole === "admin";

  const fetchDetails = async () => {
    try {
      // Fetch assistant metadata to display name
      const assistant = await fetchApi(`/assistants/${assistantId}`);
      setAssistantName(assistant.name);

      // Fetch documents list
      const docs = await fetchApi(`/documents?assistant_id=${assistantId}`);
      setDocuments(docs);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to load knowledge base details.");
    }
  };

  React.useEffect(() => {
    const token = getCookie("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const claims = decodeJwt(token);
    if (claims) {
      setIsAuthenticated(true);
      setUserRole(claims.role || "member");
    }

    const init = async () => {
      setIsLoading(true);
      await fetchDetails();
      setIsLoading(false);
    };

    if (assistantId) {
      init();
    }
  }, [assistantId]);

  const handleIngestSuccess = (newDoc: DocumentData) => {
    setDocuments((prev) => [newDoc, ...prev]);
  };

  const handleIngestError = (error: string) => {
    // Keep list fresh
    fetchDetails();
  };

  const handleRefreshList = () => {
    // Reload documents list
    fetchApi(`/documents?assistant_id=${assistantId}`)
      .then((docs) => setDocuments(docs))
      .catch((err) => console.error("Failed to refresh documents list:", err));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Loading knowledge base environment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 selection:text-white">
      
      {/* Background Gradient Orbs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-[350px] h-[350px] bg-purple-500/5 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 py-8 relative space-y-8">
        
        {/* Navigation & Header */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-850">
          <div className="space-y-1">
            <Link href="/dashboard/assistants" className="inline-flex items-center gap-2 text-xs font-semibold text-slate-450 hover:text-indigo-400 transition-colors mb-2">
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Agents
            </Link>
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shadow-lg shadow-indigo-500/5">
                <Database className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                  Knowledge Base
                  <span className="text-slate-500 font-normal text-lg">/</span>
                  <span className="text-slate-350 text-xl font-medium flex items-center gap-1.5 bg-slate-900/60 px-3 py-1 rounded-xl border border-slate-800">
                    <Bot className="h-4 w-4 text-indigo-400" />
                    {assistantName}
                  </span>
                </h1>
                <p className="text-xs font-medium text-slate-450 mt-1.5 leading-relaxed">
                  Provide custom reference documentation to augment the agent's response generation.
                </p>
              </div>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-2.5">
            <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Add Knowledge Forms (Left or Full width depending on roles) */}
          {canManage ? (
            <div className="lg:col-span-5 space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/30 border border-slate-850 shadow-2xl flex flex-col gap-6">
                
                {/* Mode Selector */}
                <div>
                  <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                    <Sparkles className="h-4.5 w-4.5 text-indigo-400" />
                    Add Knowledge Source
                  </h2>
                  <p className="text-[11px] font-semibold text-slate-500 mt-1">
                    Select the method to upload reference material.
                  </p>
                  
                  <div className="flex bg-slate-950 p-1.5 rounded-xl border border-slate-850/80 mt-4.5">
                    <button
                      onClick={() => setActiveTab("file")}
                      className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                        activeTab === "file"
                          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/10"
                          : "text-slate-450 hover:text-white"
                      }`}
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Document File
                    </button>
                    <button
                      onClick={() => setActiveTab("url")}
                      className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                        activeTab === "url"
                          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/10"
                          : "text-slate-450 hover:text-white"
                      }`}
                    >
                      <Globe className="h-3.5 w-3.5" />
                      Web URL
                    </button>
                  </div>
                </div>

                {/* Form Render */}
                <div className="pt-2">
                  {activeTab === "file" ? (
                    <FileUpload
                      assistantId={assistantId}
                      onSuccess={handleIngestSuccess}
                      onError={handleIngestError}
                    />
                  ) : (
                    <UrlIngestForm
                      assistantId={assistantId}
                      onSuccess={handleIngestSuccess}
                      onError={handleIngestError}
                    />
                  )}
                </div>

              </div>
            </div>
          ) : (
            <div className="lg:col-span-12 p-4 rounded-xl bg-slate-900/10 border border-slate-800/40 text-center text-slate-450 text-xs">
              Contact your administrator to add files or URLs to this assistant's knowledge base.
            </div>
          )}

          {/* Document list (Right) */}
          <div className={canManage ? "lg:col-span-7 space-y-4" : "lg:col-span-12 space-y-4"}>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                Indexed Documents ({documents.length})
              </h2>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshList}
                className="border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-white text-xs h-8"
              >
                Refresh Status
              </Button>
            </div>
            
            <DocumentList
              documents={documents}
              onRefresh={handleRefreshList}
              canManage={canManage}
            />
          </div>

        </div>

      </div>
    </div>
  );
}
