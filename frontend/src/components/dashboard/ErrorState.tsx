"use client";

import React from "react";
import { AlertTriangle, RefreshCw, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="bg-[#111827] border border-rose-900/60 rounded-xl p-8 max-w-2xl mx-auto my-12 text-center"
    >
      <div className="w-12 h-12 rounded-full bg-rose-950/60 border border-rose-800/60 flex items-center justify-center mx-auto mb-4 text-rose-400">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h2 className="text-xl font-semibold text-slate-100 mb-2">Unable to Load Portfolio Analytics</h2>
      <p className="text-sm text-slate-400 mb-6 font-mono break-all max-w-lg mx-auto bg-[#0B0F17] p-3 rounded-lg border border-[#1F2937]">
        {message || "An unexpected error occurred while communicating with the analytics server."}
      </p>

      <div className="flex items-center justify-center gap-4">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-200 bg-[#1F2937] hover:bg-[#374151] rounded-lg transition-colors border border-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Request
          </button>
        )}
        <Link
          href="/portfolio/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Default Dashboard
        </Link>
      </div>

      <p className="text-xs text-slate-500 mt-6">
        Ensure the backend server is running on <code className="text-slate-400">http://localhost:8000</code> and the portfolio exists in the database.
      </p>
    </div>
  );
}
