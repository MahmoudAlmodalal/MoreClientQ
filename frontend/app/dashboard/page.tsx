"use client";

import * as React from "react";
import { getCookie, eraseCookie, decodeJwt } from "@/lib/api";
import { Bot, LogOut, ShieldCheck, FileText, Send, User, Sparkles, Layers, Cpu } from "lucide-react";
import Link from "next/link";

interface MockMessage {
  sender: "user" | "assistant";
  text: string;
}

export default function DashboardPage() {
  const [tenantSlug, setTenantSlug] = React.useState<string>("unknown");
  const [userEmail, setUserEmail] = React.useState<string>("user@company.com");
  const [userRole, setUserRole] = React.useState<string>("member");
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean>(false);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);

  // Chat Widget State
  const [chatInput, setChatInput] = React.useState("");
  const [messages, setMessages] = React.useState<MockMessage[]>([
    { sender: "assistant", text: "Hello! I am your workspace assistant. How can I help you today?" }
  ]);
  const [isTyping, setIsTyping] = React.useState(false);

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
      setIsLoading(false);
    }
  }, []);

  const handleLogout = () => {
    eraseCookie("access_token");
    eraseCookie("refresh_token");
    window.location.href = "/";
  };

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setChatInput("");
    setIsTyping(true);

    // Mock AI response delay
    setTimeout(() => {
      let botResponse = "I have received your request. In the next development phase, I will retrieve and analyze details from your tenant's custom vector database storage.";
      if (userMsg.toLowerCase().includes("hello") || userMsg.toLowerCase().includes("hi")) {
        botResponse = `Hello! Welcome to the ${tenantSlug.toUpperCase()} workspace. Let me know if you need assistance with document queries or tenant resources.`;
      } else if (userMsg.toLowerCase().includes("role") || userMsg.toLowerCase().includes("who")) {
        botResponse = `You are authenticated as ${userEmail} with the role of "${userRole}". Your permissions are strictly isolated to the ${tenantSlug.toUpperCase()} tenant via row-level security.`;
      } else if (userMsg.toLowerCase().includes("help")) {
        botResponse = "You can ask me about database RLS configuration, uploaded documents, or current service quota allocations.";
      }
      
      setMessages((prev) => [...prev, { sender: "assistant", text: botResponse }]);
      setIsTyping(false);
    }, 1000);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Verifying tenant authentication context...</p>
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
              No authenticated session resolved for the <strong className="text-indigo-400 uppercase">{tenantSlug}</strong> workspace environment. Please sign in to access resources.
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
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col justify-between selection:bg-indigo-500/30">
      
      {/* Header */}
      <header className="bg-slate-900/40 border-b border-indigo-500/10 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-500">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="text-sm font-semibold tracking-tight text-white block leading-none">
                Workspace Dashboard
              </span>
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mt-1 block">
                {tenantSlug}
              </span>
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
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 hover:text-red-400 text-slate-400 text-sm font-semibold transition duration-200"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Grid Content */}
      <main className="max-w-7xl mx-auto w-full px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8 my-auto">
        
        {/* Left Side: Stats & Assets */}
        <section className="lg:col-span-7 space-y-6">
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Layers className="h-6 w-6 text-indigo-400" />
            Overview & Metrics
          </h2>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Message Quota</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-white">145</span>
                <span className="text-slate-500 text-sm">/ 500</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
                <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: "29%" }} />
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Storage Capacity</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-white">2.4</span>
                <span className="text-slate-500 text-sm">MB</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
                <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: "2.4%" }} />
              </div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Conversations</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-white">28</span>
                <span className="text-slate-500 text-sm">active</span>
              </div>
              <span className="text-[10px] text-emerald-400 font-semibold mt-2 block flex items-center gap-1">
                ● Live vector index synced
              </span>
            </div>
          </div>

          {/* Section: Ingested Documents */}
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FileText className="h-5 w-5 text-indigo-400" />
              Ingested Documents
            </h3>
            <div className="space-y-3">
              {[
                { name: "employee_handbook.pdf", size: "1.2 MB", date: "2 hours ago" },
                { name: "api_specifications.json", size: "840 KB", date: "1 day ago" },
                { name: "product_architecture.md", size: "12 KB", date: "3 days ago" }
              ].map((doc, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800/50 hover:border-slate-700/50 transition">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="text-sm font-medium text-slate-200 block">{doc.name}</span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">{doc.size}</span>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">{doc.date}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section: AI Assistants */}
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Cpu className="h-5 w-5 text-purple-400" />
                Active AI Assistants
              </h3>
              <Link href="/dashboard/assistants" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:underline transition">
                Manage Assistants &rarr;
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { name: "Document Analyst", desc: "Performs semantics search queries on ingested PDFs.", role: "Data Retrieval" },
                { name: "Code Assistant", desc: "Configured with context-aware platform programming patterns.", role: "Developer" }
              ].map((assistant, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-indigo-400" />
                    <span className="text-sm font-semibold text-slate-200">{assistant.name}</span>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">{assistant.desc}</p>
                  <span className="inline-block text-[10px] font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full uppercase">
                    {assistant.role}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Right Side: Interactive AI Assistant Simulator */}
        <section className="lg:col-span-5 flex flex-col h-[600px] bg-slate-900/40 border border-slate-800/80 rounded-2xl overflow-hidden shadow-lg">
          <div className="p-4 bg-slate-900/80 border-b border-indigo-500/10 flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center animate-pulse">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <span className="text-sm font-semibold text-slate-200 block">Workspace Assistant</span>
              <span className="text-[10px] text-emerald-400 block font-medium">● Online</span>
            </div>
          </div>

          {/* Messages list */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-slate-800">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 max-w-[85%] ${msg.sender === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}
              >
                <div className={`h-8 w-8 rounded-lg shrink-0 flex items-center justify-center ${msg.sender === "user" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300"}`}>
                  {msg.sender === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                <div className={`p-3.5 rounded-2xl text-sm leading-relaxed ${msg.sender === "user" ? "bg-indigo-600 text-white rounded-tr-none" : "bg-slate-950 border border-slate-800/80 text-slate-300 rounded-tl-none"}`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3 max-w-[85%] mr-auto">
                <div className="h-8 w-8 rounded-lg shrink-0 bg-slate-800 text-slate-300 flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800/80 text-slate-400 rounded-tl-none flex items-center gap-1">
                  <div className="h-2 w-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="h-2 w-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="h-2 w-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
          </div>

          {/* Chat Form */}
          <form onSubmit={handleSendChat} className="p-4 bg-slate-950 border-t border-slate-850 flex gap-2">
            <input
              type="text"
              value={chatInput}
              disabled={isTyping}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask anything about this tenant workspace..."
              className="flex-1 bg-slate-900 border border-slate-800 text-white text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isTyping || !chatInput.trim()}
              className="p-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50 transition"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-slate-900/20 border-t border-indigo-500/10 text-slate-500 text-xs py-4 text-center">
        Antigravity AI Platform Sandbox &copy; {new Date().getFullYear()} — Strict Database Row-Level Security active.
      </footer>
    </div>
  );
}
