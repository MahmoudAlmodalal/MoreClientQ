"use client";

import * as React from "react";
import { Link2, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";

interface UrlIngestFormProps {
  assistantId: string;
  onSuccess: (document: any) => void;
  onError: (error: string) => void;
}

export default function UrlIngestForm({ assistantId, onSuccess, onError }: UrlIngestFormProps) {
  const [url, setUrl] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Basic client-side URL validation
    try {
      new URL(url);
    } catch {
      setErrorMsg("Please enter a valid absolute URL (e.g. https://example.com).");
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const response = await fetchApi("/documents/url", {
        method: "POST",
        body: JSON.stringify({
          url: url.trim(),
          assistant_id: assistantId,
        }),
      });

      setSuccessMsg(`Successfully queued URL for ingestion! Starting background crawler...`);
      setUrl("");
      onSuccess(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to ingest URL.";
      setErrorMsg(msg);
      onError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="url-input" className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
          Public Website or Document URL
        </label>
        <div className="relative flex rounded-xl border border-slate-800 bg-slate-950/50 shadow-inner group focus-within:border-indigo-500 transition-all duration-300">
          <div className="flex items-center pl-3.5 pointer-events-none text-slate-500 group-focus-within:text-indigo-400">
            <Link2 className="h-4.5 w-4.5" />
          </div>
          <input
            id="url-input"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/documentation"
            disabled={isSubmitting}
            className="w-full bg-transparent border-0 text-white placeholder-slate-600 text-sm px-3.5 py-3 focus:outline-none focus:ring-0 disabled:text-slate-500"
            required
          />
          <div className="flex items-center pr-2">
            <Button
              type="submit"
              disabled={isSubmitting || !url.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-2 px-4 rounded-lg h-9"
            >
              {isSubmitting ? "Validating..." : "Ingest URL"}
            </Button>
          </div>
        </div>
        <p className="text-[10px] text-slate-500 font-semibold pl-1">
          The page will be reached and validated before background ingestion begins.
        </p>
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold flex items-start gap-2.5 animate-in fade-in duration-200">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-start gap-2.5 animate-in fade-in duration-200">
          <CheckCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
          <span>{successMsg}</span>
        </div>
      )}
    </form>
  );
}
