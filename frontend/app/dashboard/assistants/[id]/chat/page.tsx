import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { decodeJwt } from "@/lib/api";
import Link from "next/link";
import { ArrowLeft, Bot } from "lucide-react";

export default async function AssistantChatPage({
  params,
}: {
  params: { id: string };
}) {
  const assistantId = params.id;
  const cookieStore = cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    redirect("/login");
  }

  const claims = decodeJwt(token);
  const tenantId = claims?.tenant_id || "";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <div className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard/assistants"
            className="text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 text-sm font-medium"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Assistants
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-indigo-400" />
            <span className="text-sm font-semibold text-slate-200">AI Chat Assistant</span>
          </div>
        </div>
        {tenantId && (
          <div className="text-[10px] text-slate-500 font-mono">
            Tenant: {tenantId}
          </div>
        )}
      </div>

      {/* Main Container */}
      <div className="flex-1 max-w-4xl w-full mx-auto px-6 py-8 flex flex-col justify-center">
        <ChatWindow assistantId={assistantId} tenantId={tenantId} />
      </div>
    </div>
  );
}
