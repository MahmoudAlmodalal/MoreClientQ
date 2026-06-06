"use client";

import * as React from "react";
import { sendMessage } from "@/lib/chat-api";
import { MessageBubble, MessageType } from "./MessageBubble";
import { Send, Loader2, AlertCircle, Sparkles } from "lucide-react";

interface ChatWindowProps {
  assistantId: string;
}

export function ChatWindow({ assistantId }: ChatWindowProps) {
  const [messages, setMessages] = React.useState<MessageType[]>([]);
  const [input, setInput] = React.useState("");
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessageText = input.trim();
    setInput("");
    setError(null);

    const userMsg: MessageType = {
      role: "user",
      content: userMessageText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendMessage(assistantId, conversationId, userMessageText);
      
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const assistantMsg: MessageType = {
        role: "assistant",
        content: response.content,
        sources: response.sources,
        model_used: response.model_used,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Failed to send message:", err);
      setError(err?.message || "An error occurred while communicating with the assistant.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-semibold text-slate-100">AI Assistant Session</span>
        </div>
        {conversationId && (
          <span className="text-[10px] text-slate-500 font-mono">
            Session: {conversationId.substring(0, 8)}...
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-slate-200 font-medium text-sm">Start a Conversation</h3>
            <p className="text-slate-400 text-xs max-w-[280px]">
              Ask a question to query your assistant. The response will be grounded using files in the assistant's knowledge base.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
          ))
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex w-full justify-start my-3">
            <div className="flex gap-3 max-w-[80%] items-start">
              <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 text-indigo-400 flex items-center justify-center shrink-0">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <div className="bg-slate-900 border border-slate-800 text-slate-350 rounded-2xl rounded-tl-none px-4 py-2.5 shadow-md flex items-center gap-2">
                <span className="text-xs text-slate-400">Generating grounded response...</span>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex items-center gap-2.5 p-4 border border-rose-500/20 bg-rose-500/5 text-rose-400 text-xs rounded-xl">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <div className="flex-1">
              <span className="font-semibold">Chat Error: </span>
              {error}
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-4 bg-slate-900/60 border-t border-slate-800 flex gap-3 items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your knowledge base documents..."
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-slate-200 text-sm placeholder-slate-500 rounded-xl px-4 py-3 outline-none transition-all"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="bg-indigo-600 hover:bg-indigo-500 text-white p-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0 flex items-center justify-center"
          disabled={isLoading || !input.trim()}
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
