"use client";

import * as React from "react";
import { Plus, Sparkles, Copy, Check, HelpCircle } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { AssistantData } from "./assistant-form";

interface EmbedCodeModalProps {
  assistant: AssistantData;
  onClose: () => void;
}

export default function EmbedCodeModal({ assistant, onClose }: EmbedCodeModalProps) {
  const [snippet, setSnippet] = React.useState<string>("");
  const [isLoading, setIsLoading] = React.useState(true);
  const [isCopied, setIsCopied] = React.useState(false);

  React.useEffect(() => {
    const fetchEmbedCode = async () => {
      setIsLoading(true);
      try {
        const data = await fetchApi(`/assistants/${assistant.id}/embed`);
        setSnippet(data.snippet);
      } catch (err: unknown) {
        setSnippet(
          "Failed to retrieve embed code: " +
            (err instanceof Error ? err.message : "Unknown error")
        );
      } finally {
        setIsLoading(false);
      }
    };

    if (assistant.id) {
      fetchEmbedCode();
    }
  }, [assistant.id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(snippet);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
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
            onClick={onClose}
            className="text-slate-400 hover:text-white transition duration-200 rounded-lg p-1 hover:bg-slate-800"
          >
            <Plus className="h-5 w-5 rotate-45" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-slate-400 text-xs leading-relaxed">
            Add this copy-pasteable script tag to the HTML body of your website or application. This will render the chat widget bubble automatically.
          </p>

          {isLoading ? (
            <div className="h-32 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-center">
              <div className="h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="relative group">
              <pre className="bg-slate-950 border border-slate-850 p-4 rounded-xl text-indigo-300 text-xs overflow-x-auto font-mono max-w-full">
                {snippet}
              </pre>
              <button
                onClick={handleCopy}
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
              The widget loads and executes client side. RLS access control ensures it can only access data vectors configured for the <strong>{assistant.name}</strong> bot.
            </span>
          </div>
        </div>

        <div className="p-6 border-t border-slate-800 flex items-center justify-end bg-slate-950/40">
          <Button
            onClick={onClose}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
          >
            Close Dialog
          </Button>
        </div>
      </div>
    </div>
  );
}
