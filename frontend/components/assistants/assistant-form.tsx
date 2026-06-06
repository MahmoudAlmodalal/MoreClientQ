"use client";

import * as React from "react";
import { X, Sparkles, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface AssistantData {
  id?: string;
  name: string;
  system_prompt: string;
  model: string;
  temperature: number;
  max_tokens: number;
  is_active?: boolean;
}

interface AssistantFormProps {
  initialData?: AssistantData;
  onSubmit: (data: AssistantData) => Promise<void>;
  onClose: () => void;
  title: string;
}

export default function AssistantForm({
  initialData,
  onSubmit,
  onClose,
  title,
}: AssistantFormProps) {
  const [name, setName] = React.useState(initialData?.name || "");
  const [systemPrompt, setSystemPrompt] = React.useState(initialData?.system_prompt || "");
  const [model, setModel] = React.useState(initialData?.model || "gpt-4o-mini");
  const [temperature, setTemperature] = React.useState(initialData?.temperature ?? 0.7);
  const [maxTokens, setMaxTokens] = React.useState(initialData?.max_tokens ?? 1024);
  const [isActive, setIsActive] = React.useState(initialData?.is_active ?? true);
  
  const [error, setError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!name.trim()) {
      setError("Assistant name is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        system_prompt: systemPrompt.trim(),
        model,
        temperature: parseFloat(temperature.toString()),
        max_tokens: parseInt(maxTokens.toString(), 10),
        is_active: isActive,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save assistant.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="text-slate-400 hover:text-white transition duration-200 rounded-lg p-1 hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-2.5">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Name */}
          <div className="space-y-1.5">
            <label htmlFor="assistant-name" className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Assistant Name <span className="text-red-400">*</span>
            </label>
            <input
              id="assistant-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Support Bot"
              className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200 placeholder:text-slate-600 text-sm"
              disabled={isSubmitting}
            />
          </div>

          {/* Model Selection */}
          <div className="space-y-1.5">
            <label htmlFor="assistant-model" className="text-xs font-bold uppercase tracking-wider text-slate-400">
              AI Model
            </label>
            <select
              id="assistant-model"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200 text-sm"
              disabled={isSubmitting}
            >
              <option value="gpt-4o-mini">gpt-4o-mini (Fast & Cost-Effective)</option>
              <option value="gpt-4o">gpt-4o (High-Intelligence Reasoning)</option>
              <option value="claude-3-5-sonnet">claude-3-5-sonnet (Advanced Coding & Logic)</option>
            </select>
          </div>

          {/* System Prompt */}
          <div className="space-y-1.5">
            <label htmlFor="assistant-prompt" className="text-xs font-bold uppercase tracking-wider text-slate-400">
              System Instructions / Persona
            </label>
            <textarea
              id="assistant-prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Define the behavior, tone, restrictions, and core responsibilities of your AI agent..."
              rows={4}
              className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200 placeholder:text-slate-600 text-sm resize-none"
              disabled={isSubmitting}
            />
          </div>

          {/* Sliders Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Temperature */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="assistant-temp" className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Temperature
                </label>
                <span className="text-xs font-bold text-indigo-400">{temperature}</span>
              </div>
              <input
                id="assistant-temp"
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                disabled={isSubmitting}
              />
              <span className="text-[10px] text-slate-500 block leading-tight">
                Lower values are deterministic; higher values are creative.
              </span>
            </div>

            {/* Max Tokens */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="assistant-tokens" className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Max Response Tokens
                </label>
                <span className="text-xs font-bold text-indigo-400">{maxTokens}</span>
              </div>
              <input
                id="assistant-tokens"
                type="number"
                min="1"
                max="8192"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value, 10) || 1)}
                className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition duration-200 text-sm font-semibold"
                disabled={isSubmitting}
              />
              <span className="text-[10px] text-slate-500 block leading-tight">
                Controls the maximum size of generated responses.
              </span>
            </div>
          </div>

          {initialData && (
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-850">
              <input
                id="assistant-active"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4.5 w-4.5 rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                disabled={isSubmitting}
              />
              <div>
                <label htmlFor="assistant-active" className="text-sm font-semibold text-slate-200 cursor-pointer block leading-none">
                  Enable Assistant
                </label>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Inactive assistants will not accept user conversations or widget queries.
                </span>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800 flex items-center justify-end gap-3 bg-slate-950/40">
          <Button
            type="button"
            onClick={onClose}
            variant="outline"
            className="border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white"
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            onClick={handleSubmit}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-lg shadow-indigo-600/20"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Saving..." : initialData ? "Update Assistant" : "Create Assistant"}
          </Button>
        </div>

      </div>
    </div>
  );
}
