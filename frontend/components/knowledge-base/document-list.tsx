"use client";

import * as React from "react";
import { FileText, Link2, Clock, CheckCircle2, XCircle, Trash2, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";

export interface DocumentData {
  id: string;
  assistant_id: string;
  filename: string;
  file_type: "pdf" | "docx" | "txt" | "url";
  status: "pending" | "processing" | "ready" | "failed";
  chunk_count: number | null;
  error_message: string | null;
  created_at: string;
}

interface DocumentListProps {
  documents: DocumentData[];
  onRefresh: () => void;
  canManage: boolean;
}

export default function DocumentList({ documents, onRefresh, canManage }: DocumentListProps) {
  const [localDocs, setLocalDocs] = React.useState<DocumentData[]>(documents);
  const [isDeletingId, setIsDeletingId] = React.useState<string | null>(null);

  // Sync prop changes to local state
  React.useEffect(() => {
    setLocalDocs(documents);
  }, [documents]);

  // Polling for processing/pending documents
  React.useEffect(() => {
    const activePollingDocs = localDocs.filter(
      (doc) => doc.status === "pending" || doc.status === "processing"
    );

    if (activePollingDocs.length === 0) return;

    const intervalId = setInterval(async () => {
      let hasUpdates = false;
      const updatedDocs = [...localDocs];

      await Promise.all(
        activePollingDocs.map(async (doc) => {
          try {
            const statusUpdate = await fetchApi(`/documents/${doc.id}/status`);
            
            // Check if status changed
            const index = updatedDocs.findIndex((d) => d.id === doc.id);
            if (index !== -1 && (
              updatedDocs[index].status !== statusUpdate.status || 
              updatedDocs[index].chunk_count !== statusUpdate.chunk_count ||
              updatedDocs[index].error_message !== statusUpdate.error_message
            )) {
              updatedDocs[index] = {
                ...updatedDocs[index],
                status: statusUpdate.status,
                chunk_count: statusUpdate.chunk_count,
                error_message: statusUpdate.error_message,
              };
              hasUpdates = true;
            }
          } catch (err) {
            console.error(`Failed to poll status for document ${doc.id}:`, err);
          }
        })
      );

      if (hasUpdates) {
        setLocalDocs(updatedDocs);
        // Call parent onRefresh to keep parent in sync if necessary
        onRefresh();
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(intervalId);
  }, [localDocs, onRefresh]);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to remove "${name}" from the knowledge base?`)) {
      return;
    }

    setIsDeletingId(id);
    try {
      await fetchApi(`/documents/${id}`, {
        method: "DELETE",
      });
      setLocalDocs((prev) => prev.filter((doc) => doc.id !== id));
      onRefresh();
    } catch (err: any) {
      alert(err.message || "Failed to delete document.");
    } finally {
      setIsDeletingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
            <Clock className="h-3 w-3 animate-pulse" />
            Queued
          </span>
        );
      case "processing":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
            Processing
          </span>
        );
      case "ready":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-3 w-3" />
            Ready
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  if (localDocs.length === 0) {
    return (
      <div className="py-12 px-4 rounded-2xl border border-slate-800 bg-slate-900/10 text-center space-y-3">
        <HelpCircle className="h-10 w-10 text-slate-650 mx-auto" />
        <div className="space-y-1">
          <p className="text-white text-sm font-bold">No documents indexed</p>
          <p className="text-slate-500 text-xs max-w-sm mx-auto leading-relaxed">
            Upload files or add website URLs to build this assistant's retrieval knowledge base.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-850 bg-slate-950/20 shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-850 bg-slate-950/50 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              <th className="py-4.5 px-6">Name / Source</th>
              <th className="py-4.5 px-6">Type</th>
              <th className="py-4.5 px-6">Status</th>
              <th className="py-4.5 px-6">Indexed Chunks</th>
              <th className="py-4.5 px-6">Added At</th>
              {canManage && <th className="py-4.5 px-6 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850/60">
            {localDocs.map((doc) => {
              const isUrl = doc.file_type === "url";
              return (
                <tr
                  key={doc.id}
                  className="text-xs hover:bg-slate-900/10 transition-colors"
                >
                  {/* Filename / URL */}
                  <td className="py-4 px-6 font-medium text-white max-w-[280px]">
                    {isUrl ? (
                      <a
                        href={doc.filename}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:underline flex items-center gap-1.5 truncate"
                      >
                        <Link2 className="h-3.5 w-3.5 shrink-0" />
                        {doc.filename}
                      </a>
                    ) : (
                      <span className="flex items-center gap-1.5 truncate text-slate-200">
                        <FileText className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                        {doc.filename}
                      </span>
                    )}
                    {doc.error_message && (
                      <span className="block text-[10px] text-red-400 mt-1 font-semibold leading-relaxed">
                        Reason: {doc.error_message}
                      </span>
                    )}
                  </td>

                  {/* File Type */}
                  <td className="py-4 px-6 uppercase font-bold tracking-wider text-[10px] text-slate-400">
                    {doc.file_type}
                  </td>

                  {/* Status Badge */}
                  <td className="py-4 px-6">{getStatusBadge(doc.status)}</td>

                  {/* Chunk Count */}
                  <td className="py-4 px-6 text-slate-300 font-semibold">
                    {doc.chunk_count !== null ? doc.chunk_count : "—"}
                  </td>

                  {/* Created Date */}
                  <td className="py-4 px-6 text-slate-550 font-medium">
                    {new Date(doc.created_at).toLocaleString()}
                  </td>

                  {/* Actions (Delete) */}
                  {canManage && (
                    <td className="py-4 px-6 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        disabled={isDeletingId === doc.id}
                        className="border-slate-800 text-slate-500 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 h-8 px-2.5"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
