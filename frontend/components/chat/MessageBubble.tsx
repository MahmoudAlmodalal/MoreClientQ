import * as React from "react";
import { SourceReference } from "@/lib/chat-api";
import { FileText, Sparkles, User } from "lucide-react";

export interface MessageType {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: SourceReference[];
  model_used?: string | null;
}

interface MessageBubbleProps {
  message: MessageType;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (message.role === "system") {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-slate-850 border border-slate-700/40 text-slate-400 text-xs px-3 py-1 rounded-full font-mono">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex w-full my-3 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
        {/* Avatar */}
        <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 border shadow-inner ${
          isUser 
            ? "bg-indigo-600 border-indigo-500 text-indigo-100" 
            : "bg-slate-800 border-slate-700 text-emerald-400"
        }`}>
          {isUser ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
        </div>

        {/* Message Bubble */}
        <div className="flex flex-col gap-1.5">
          <div className={`rounded-2xl px-4 py-2.5 shadow-md text-sm leading-relaxed ${
            isUser 
              ? "bg-indigo-600 text-white rounded-tr-none" 
              : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none"
          }`}>
            <p className="whitespace-pre-wrap">{message.content}</p>

            {/* Model Badge */}
            {!isUser && message.model_used && (
              <div className="mt-2 flex items-center gap-1 text-[10px] text-slate-500 font-mono">
                <span>Model: {message.model_used}</span>
              </div>
            )}
          </div>

          {/* Sources Footnotes */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="flex flex-col gap-1 mt-1 px-1">
              <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                <FileText className="h-3 w-3 text-indigo-400" /> Grounded Sources:
              </span>
              <div className="flex flex-wrap gap-2 mt-0.5">
                {message.sources.map((src, idx) => (
                  <div 
                    key={idx}
                    className="bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 rounded-lg p-2 text-[11px] text-slate-300 max-w-[220px] transition-all flex flex-col gap-1"
                    title={`Score: ${(src.score * 100).toFixed(0)}%`}
                  >
                    <div className="flex items-center justify-between gap-2 border-b border-slate-800/60 pb-1">
                      <span className="font-mono text-[9px] text-slate-500 truncate">
                        Doc: {src.document_id.substring(0, 8)}
                      </span>
                      <span className="text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 px-1 rounded">
                        {(src.score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="line-clamp-2 italic text-slate-400 text-[10px] leading-normal">
                      "{src.chunk_text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
