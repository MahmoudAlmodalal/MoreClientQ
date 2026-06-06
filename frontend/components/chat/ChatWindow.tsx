"use client";

import * as React from "react";
import { sendMessage, createWebSocket } from "@/lib/chat-api";
import { getCookie, decodeJwt } from "@/lib/api";
import { MessageBubble, MessageType } from "./MessageBubble";
import { StreamingDot } from "./StreamingDot";
import { HandoffBanner } from "./HandoffBanner";
import { Send, Loader2, AlertCircle, Sparkles, Wifi, WifiOff } from "lucide-react";

interface ChatWindowProps {
  assistantId: string;
  tenantId?: string;
}

type WSState = "connecting" | "open" | "closed" | "error";

export function ChatWindow({ assistantId, tenantId }: ChatWindowProps) {
  const [messages, setMessages] = React.useState<MessageType[]>([]);
  const [input, setInput] = React.useState("");
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isStreaming, setIsStreaming] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isHandoff, setIsHandoff] = React.useState(false);
  const [wsState, setWsState] = React.useState<WSState>("connecting");

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const wsRef = React.useRef<WebSocket | null>(null);
  const streamingIndexRef = React.useRef<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // ── WebSocket lifecycle ──────────────────────────────────────────────────
  React.useEffect(() => {
    const token = getCookie("access_token");
    if (!token) {
      setWsState("error");
      return;
    }

    // Use the tenantId prop if provided (passed from the server component);
    // fall back to decoding it from the JWT for resilience.
    const claims = decodeJwt(token);
    const resolvedTenantId: string = tenantId || claims?.tenant_id || "";
    if (!resolvedTenantId) {
      setWsState("error");
      return;
    }

    let ws: WebSocket;
    try {
      ws = createWebSocket(assistantId, resolvedTenantId, token);
    } catch {
      setWsState("error");
      return;
    }

    wsRef.current = ws;
    setWsState("connecting");

    ws.onopen = () => {
      setWsState("open");
    };

    ws.onerror = () => {
      setWsState("error");
    };

    ws.onclose = (ev) => {
      setWsState("closed");
      // If mid-stream, finalise the streaming bubble
      if (isStreaming) {
        setIsStreaming(false);
        setIsLoading(false);
        streamingIndexRef.current = null;
      }
    };

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);

        switch (data.type) {
          case "token": {
            const delta: string = data.delta ?? "";
            setMessages((prev) => {
              const idx = streamingIndexRef.current;
              if (idx === null) return prev;
              const updated = [...prev];
              updated[idx] = {
                ...updated[idx],
                content: (updated[idx].content ?? "") + delta,
              };
              return updated;
            });
            break;
          }

          case "done": {
            const convId: string = data.conversation_id ?? "";
            const msgId: string = data.message_id ?? "";
            const sources = data.sources ?? [];
            const modelUsed: string | undefined = data.model_used;

            if (!conversationId && convId) setConversationId(convId);

            setMessages((prev) => {
              const idx = streamingIndexRef.current;
              if (idx === null) return prev;
              const updated = [...prev];
              updated[idx] = {
                ...updated[idx],
                sources,
                model_used: modelUsed,
              };
              return updated;
            });

            streamingIndexRef.current = null;
            setIsStreaming(false);
            setIsLoading(false);
            break;
          }

          case "error": {
            const code: string = data.code ?? "error";
            const detail: string = data.detail ?? "An error occurred.";
            setError(`[${code}] ${detail}`);
            streamingIndexRef.current = null;
            setIsStreaming(false);
            setIsLoading(false);
            break;
          }

          case "handoff": {
            const convId: string = data.conversation_id ?? "";
            if (!conversationId && convId) setConversationId(convId);
            setIsHandoff(true);
            streamingIndexRef.current = null;
            setIsStreaming(false);
            setIsLoading(false);
            break;
          }

          case "pong":
            break;

          default:
            break;
        }
      } catch {
        // Non-JSON or unexpected frame — ignore
      }
    };

    return () => {
      ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assistantId]);

  // ── Ping keepalive every 25s ─────────────────────────────────────────────
  React.useEffect(() => {
    if (wsState !== "open") return;
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 25_000);
    return () => clearInterval(interval);
  }, [wsState]);

  // ── Send a message ────────────────────────────────────────────────────────
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || isHandoff) return;

    const userMessageText = input.trim();
    setInput("");
    setError(null);

    const userMsg: MessageType = { role: "user", content: userMessageText };
    setMessages((prev) => [...prev, userMsg]);

    // Optimistically add an empty assistant bubble for streaming
    const assistantPlaceholder: MessageType = { role: "assistant", content: "" };
    setMessages((prev) => {
      streamingIndexRef.current = prev.length;
      return [...prev, assistantPlaceholder];
    });

    setIsLoading(true);

    // ── Primary: WebSocket ──
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      setIsStreaming(true);
      ws.send(
        JSON.stringify({
          type: "message",
          conversation_id: conversationId ?? null,
          content: userMessageText,
        })
      );
      // Response is handled by ws.onmessage; no further action here
      return;
    }

    // ── Fallback: REST ──
    setIsStreaming(false);
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
      // Update the optimistic placeholder bubble in-place instead of appending
      setMessages((prev) => {
        const idx = streamingIndexRef.current;
        if (idx === null) return [...prev, assistantMsg];
        const updated = [...prev];
        updated[idx] = assistantMsg;
        streamingIndexRef.current = null;
        return updated;
      });
      setConversationId((prev) => prev ?? response.conversation_id ?? null);
    } catch (err: any) {
      console.error("Failed to send message:", err);
      // Map well-known HTTP status codes to friendly messages
      const status = err?.status ?? err?.response?.status;
      if (status === 409) {
        setError(
          "This conversation has been handed off to a human agent. AI responses are paused."
        );
        setIsHandoff(true);
      } else if (status === 429) {
        setError("Your usage quota has been reached. Please try again in the next hour.");
      } else if (status === 503) {
        setError("The AI service is temporarily unavailable. Please try again shortly.");
      } else {
        setError(
          err?.data?.detail ||
            err?.message ||
            "An error occurred while communicating with the assistant."
        );
      }
      // Remove placeholder bubble on REST failure
      setMessages((prev) => {
        const idx = streamingIndexRef.current;
        if (idx === null) return prev;
        streamingIndexRef.current = null;
        return prev.filter((_, i) => i !== idx);
      });
    } finally {
      setIsLoading(false);
    }
  };

  // ── WS status badge ───────────────────────────────────────────────────────
  const wsStatusBadge = () => {
    if (wsState === "open") {
      return (
        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
          <Wifi className="h-3 w-3" /> Live
        </span>
      );
    }
    if (wsState === "connecting") {
      return (
        <span className="flex items-center gap-1 text-[10px] text-amber-400 font-medium">
          <Loader2 className="h-3 w-3 animate-spin" /> Connecting…
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1 text-[10px] text-slate-500 font-medium">
        <WifiOff className="h-3 w-3" /> REST fallback
      </span>
    );
  };

  const inputDisabled = isLoading || isHandoff;

  return (
    <div className="flex flex-col h-[600px] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-semibold text-slate-100">AI Assistant Session</span>
        </div>
        <div className="flex items-center gap-4">
          {wsStatusBadge()}
          {conversationId && (
            <span className="text-[10px] text-slate-500 font-mono">
              Session: {conversationId.substring(0, 8)}…
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && !isLoading ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
            <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-slate-200 font-medium text-sm">Start a Conversation</h3>
            <p className="text-slate-400 text-xs max-w-[280px]">
              Ask a question to query your assistant. The response will be grounded using files in
              the assistant's knowledge base.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            // For the streaming assistant bubble, show StreamingDot while content is empty
            const isStreamingBubble =
              isStreaming &&
              index === streamingIndexRef.current &&
              msg.role === "assistant";
            return (
              <MessageBubble
                key={index}
                message={msg}
                streamingIndicator={isStreamingBubble && msg.content === "" ? <StreamingDot /> : undefined}
              />
            );
          })
        )}

        {/* REST loading state (WebSocket fallback) */}
        {isLoading && !isStreaming && (
          <div className="flex w-full justify-start my-3">
            <div className="flex gap-3 max-w-[80%] items-start">
              <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 text-indigo-400 flex items-center justify-center shrink-0">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <div className="bg-slate-900 border border-slate-800 text-slate-350 rounded-2xl rounded-tl-none px-4 py-2.5 shadow-md flex items-center gap-2">
                <span className="text-xs text-slate-400">Generating grounded response…</span>
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

      {/* Handoff Banner */}
      {isHandoff && <HandoffBanner />}

      {/* Input Form */}
      <form
        onSubmit={handleSend}
        className="p-4 bg-slate-900/60 border-t border-slate-800 flex gap-3 items-center"
      >
        <input
          id="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isHandoff
              ? "Conversation transferred to a human agent…"
              : "Ask a question about your knowledge base documents…"
          }
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-slate-200 text-sm placeholder-slate-500 rounded-xl px-4 py-3 outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={inputDisabled}
        />
        <button
          id="chat-send-button"
          type="submit"
          className="bg-indigo-600 hover:bg-indigo-500 text-white p-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0 flex items-center justify-center"
          disabled={inputDisabled || !input.trim()}
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
