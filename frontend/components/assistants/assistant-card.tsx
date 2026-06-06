"use client";

import * as React from "react";
import { Bot, Settings, Trash2, Database, Code, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AssistantData } from "./assistant-form";
import Link from "next/link";

interface AssistantCardProps {
  assistant: AssistantData;
  onEdit: (assistant: AssistantData) => void;
  onDelete: (id: string) => Promise<void>;
  onShowEmbed: (assistant: AssistantData) => void;
}

export default function AssistantCard({
  assistant,
  onEdit,
  onDelete,
  onShowEmbed,
}: AssistantCardProps) {
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);

  const handleDelete = async () => {
    if (!assistant.id) return;
    if (!confirm(`Are you sure you want to delete "${assistant.name}"? This action is permanent.`)) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);
    try {
      await onDelete(assistant.id);
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete assistant.");
      setIsDeleting(false);
    }
  };

  return (
    <div className="relative p-6 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-indigo-500/30 transition duration-300 flex flex-col justify-between group shadow-xl">
      
      {/* Active Indicator & Name */}
      <div className="space-y-3.5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl bg-slate-950 border ${assistant.is_active ? "border-indigo-500/20 text-indigo-400" : "border-slate-850 text-slate-500"}`}>
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-white tracking-tight text-base leading-tight group-hover:text-indigo-400 transition-colors">
                {assistant.name}
              </h3>
              <span className="text-[10px] text-slate-500 font-medium block mt-0.5">
                ID: {assistant.id}
              </span>
            </div>
          </div>
          <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${assistant.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-800 text-slate-500"}`}>
            {assistant.is_active ? "Active" : "Inactive"}
          </span>
        </div>

        {/* Details List */}
        <p className="text-slate-400 text-xs leading-relaxed line-clamp-2 min-h-[2rem]">
          {assistant.system_prompt || "No system prompt configured."}
        </p>

        <div className="grid grid-cols-2 gap-3 py-2 border-y border-slate-850 text-[11px] font-semibold text-slate-400">
          <div>
            <span className="text-slate-500 block uppercase text-[9px] font-bold tracking-wider">Model</span>
            <span className="text-slate-200 mt-0.5 block truncate">{assistant.model}</span>
          </div>
          <div>
            <span className="text-slate-500 block uppercase text-[9px] font-bold tracking-wider">Temperature</span>
            <span className="text-slate-200 mt-0.5 block">{assistant.temperature}</span>
          </div>
          <div>
            <span className="text-slate-500 block uppercase text-[9px] font-bold tracking-wider">Max Tokens</span>
            <span className="text-slate-200 mt-0.5 block">{assistant.max_tokens}</span>
          </div>
        </div>
      </div>

      {/* Delete error notification */}
      {deleteError && (
        <div className="mt-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-start gap-2 animate-in fade-in duration-200">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{deleteError}</span>
        </div>
      )}

      {/* Actions */}
      <div className="mt-5 pt-4 border-t border-slate-850 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Link href={`/dashboard/assistants/${assistant.id}/knowledge-base`}>
            <Button
              variant="outline"
              size="sm"
              className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white px-3 flex items-center gap-1.5"
            >
              <Database className="h-3.5 w-3.5" />
              <span>KB</span>
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onShowEmbed(assistant)}
            className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white px-3 flex items-center gap-1.5"
          >
            <Code className="h-3.5 w-3.5" />
            <span>Embed</span>
          </Button>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(assistant)}
            className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white px-2.5"
            disabled={isDeleting}
          >
            <Settings className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDelete}
            className="border-slate-800 text-red-400 hover:bg-red-500/10 hover:text-red-400 px-2.5 hover:border-red-500/20"
            disabled={isDeleting}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

    </div>
  );
}
