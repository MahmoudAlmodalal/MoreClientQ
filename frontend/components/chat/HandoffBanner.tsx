"use client";

import { UserCheck, PhoneCall } from "lucide-react";

interface HandoffBannerProps {
  /** Optional custom message override */
  message?: string;
}

/**
 * HandoffBanner — notification banner displayed when a conversation
 * enters handoff state, informing the user that a human agent has been notified.
 * Disabling the input is handled by the parent ChatWindow.
 */
export function HandoffBanner({ message }: HandoffBannerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="mx-4 mb-4 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 shadow-md"
    >
      {/* Icon cluster */}
      <div className="mt-0.5 flex shrink-0 items-center justify-center rounded-lg bg-amber-500/20 p-1.5">
        <UserCheck className="h-4 w-4 text-amber-400" />
      </div>

      {/* Text */}
      <div className="flex-1 space-y-0.5">
        <p className="text-sm font-semibold text-amber-300">Transferred to a Human Agent</p>
        <p className="text-xs leading-relaxed text-amber-400/80">
          {message ??
            "A human support agent has been notified and will join this conversation shortly. Further AI responses are paused."}
        </p>
      </div>

      {/* Indicator */}
      <div className="mt-0.5 shrink-0">
        <PhoneCall className="h-4 w-4 animate-pulse text-amber-400" />
      </div>
    </div>
  );
}
