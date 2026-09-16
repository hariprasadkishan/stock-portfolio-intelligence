"use client";

import React, { useState, useRef, KeyboardEvent } from "react";
import { askPortfolioAnalyst } from "@/lib/api";
import { AnalystResponse } from "@/lib/types";
import {
  Sparkles,
  Send,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";

interface AIAnalystProps {
  portfolioId: string;
  portfolioName?: string;
}

const SUGGESTED_QUESTIONS: string[] = [
  "Why did my portfolio underperform the benchmark?",
  "What are the biggest sources of risk in my portfolio?",
  "Explain my portfolio concentration.",
  "Which holdings contributed most to my returns?",
  "How diversified is my portfolio?",
];

const METRIC_LABELS: Record<string, string> = {
  initial_cash: "Initial Cash",
  available_cash: "Available Cash",
  current_portfolio_value: "Portfolio Value",
  invested_value: "Invested Capital",
  absolute_pnl: "Absolute P&L",
  percentage_pnl: "Percentage P&L",
  cumulative_return: "Cumulative Return",
  annualized_return: "Annualized Return",
  annualized_volatility: "Annualized Volatility",
  sharpe_ratio: "Sharpe Ratio",
  sortino_ratio: "Sortino Ratio",
  maximum_drawdown: "Maximum Drawdown",
  maximum_drawdown_duration: "Drawdown Duration",
  var_95: "Value at Risk (95%)",
  cvar_95: "Conditional VaR (95%)",
  beta: "Beta",
  alpha: "Jensen's Alpha",
  tracking_error: "Tracking Error",
  information_ratio: "Information Ratio",
  benchmark_portfolio_return: "Portfolio Return",
  benchmark_cumulative_return: "Benchmark Return",
  active_return: "Active Return",
  asset_allocation: "Asset Allocation",
  sector_exposure: "Sector Exposure",
  concentration_analytics: "Concentration Analytics",
  return_contribution: "Return Contributions",
  correlation_matrix: "Correlation Matrix",
};

export function AIAnalyst({ portfolioId, portfolioName }: AIAnalystProps) {
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSubmittedQuestion, setLastSubmittedQuestion] = useState<string>("");
  const [response, setResponse] = useState<AnalystResponse | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmedQuestion = question.trim();
  const charCount = question.length;
  const isOverLimit = charCount > 1000;
  const canSubmit = trimmedQuestion.length > 0 && !isOverLimit && !isLoading;

  const handleSubmit = async (qToSubmit?: string) => {
    const textToAsk = (qToSubmit !== undefined ? qToSubmit : question).trim();
    if (!textToAsk || textToAsk.length > 1000 || isLoading) return;

    setIsLoading(true);
    setError(null);
    setLastSubmittedQuestion(textToAsk);

    try {
      const data = await askPortfolioAnalyst(portfolioId, textToAsk);
      setResponse(data);
      // Keep question in input or allow user to ask follow-up
    } catch (err: any) {
      console.error("AI Analyst request error:", err);
      const msg =
        err?.message ||
        "Unable to retrieve AI analysis at this time. Please verify backend service and retry.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) {
        handleSubmit();
      }
    }
  };

  const handleSelectSuggested = (q: string) => {
    setQuestion(q);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleRetry = () => {
    if (lastSubmittedQuestion) {
      handleSubmit(lastSubmittedQuestion);
    } else if (trimmedQuestion) {
      handleSubmit(trimmedQuestion);
    }
  };

  return (
    <section
      aria-labelledby="ai-analyst-heading"
      className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 md:p-6 shadow-sm transition-colors hover:border-slate-700"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1F2937] gap-3">
        <div className="flex items-start sm:items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-950/60 border border-blue-800/60 text-blue-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2
                id="ai-analyst-heading"
                className="text-lg font-semibold text-slate-100 tracking-tight"
              >
                AI Financial Analyst
              </h2>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 border border-blue-700/50">
                Deterministic Grounding
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Ask questions about your portfolio&apos;s performance, risk, allocation, and diversification.
            </p>
          </div>
        </div>

        {portfolioName && (
          <div className="text-xs font-mono text-slate-400 bg-[#0B0F17] px-3 py-1.5 rounded-md border border-[#1F2937] self-start sm:self-auto">
            Context: <span className="text-slate-200 font-semibold">{portfolioName}</span>
          </div>
        )}
      </div>

      {/* Suggested Questions Chips */}
      <div className="pt-4 pb-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-2.5">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
          <span>Suggested analytical inquiries:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectSuggested(q)}
              disabled={isLoading}
              className="text-xs text-slate-300 bg-[#0B0F17] hover:bg-[#1F2937] hover:text-white border border-[#1F2937] hover:border-slate-600 px-3 py-1.5 rounded-full transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
            >
              &ldquo;{q}&rdquo;
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="mt-3 relative">
        <label htmlFor="ai-analyst-input" className="sr-only">
          Ask a question about your portfolio
        </label>
        <textarea
          ref={textareaRef}
          id="ai-analyst-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={3}
          maxLength={1000}
          placeholder="e.g. Why did my portfolio underperform the benchmark this quarter? (Press Enter to submit, Shift+Enter for newline)"
          className={`w-full bg-[#0B0F17] text-slate-100 text-sm rounded-lg p-3.5 border transition-colors outline-none focus:ring-1 resize-y min-h-[85px] max-h-[220px] placeholder:text-slate-500 disabled:opacity-60 disabled:cursor-not-allowed ${
            isOverLimit
              ? "border-rose-600 focus:ring-rose-500"
              : "border-[#1F2937] focus:border-blue-500 focus:ring-blue-500"
          }`}
        />

        {/* Input Controls Bar */}
        <div className="flex items-center justify-between mt-2 pt-1 text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-[11px] ${
                isOverLimit
                  ? "text-rose-400 font-semibold"
                  : charCount > 900
                  ? "text-amber-400"
                  : "text-slate-500"
              }`}
            >
              {charCount} / 1000 characters
            </span>
            <span className="hidden sm:inline text-slate-500">•</span>
            <span className="hidden sm:inline text-slate-500 text-[11px]">
              Strictly grounded in verified Python financial metrics
            </span>
          </div>

          <div className="flex items-center gap-2">
            {response && (
              <button
                type="button"
                onClick={() => {
                  setResponse(null);
                  setError(null);
                }}
                className="text-slate-400 hover:text-slate-200 text-xs px-2.5 py-1.5 rounded transition-colors"
              >
                Clear Result
              </button>
            )}
            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Ask Analyst</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Loading State Banner */}
      {isLoading && (
        <div className="mt-5 p-4 rounded-lg bg-[#0B0F17] border border-blue-900/40 text-blue-300 flex items-center gap-3 animate-pulse">
          <RefreshCw className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
          <div className="text-xs">
            <p className="font-medium text-slate-200">
              Consulting deterministic portfolio analytics engine...
            </p>
            <p className="text-slate-400 text-[11px] mt-0.5">
              Evaluating risk, returns, sector exposures, and concentration against configured benchmark.
            </p>
          </div>
        </div>
      )}

      {/* Error State Banner */}
      {error && !isLoading && (
        <div className="mt-5 p-4 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
            <div className="text-xs">
              <p className="font-semibold text-rose-100">Unable to generate analysis</p>
              <p className="text-rose-300/90 mt-0.5">{error}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRetry}
            className="self-start sm:self-center inline-flex items-center gap-1.5 text-xs bg-rose-900/60 hover:bg-rose-800 text-white px-3 py-1.5 rounded border border-rose-700 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Success State Response Area */}
      {response && !isLoading && (
        <div className="mt-5 rounded-lg bg-[#0B0F17] border border-[#1F2937] p-4 md:p-5 space-y-4">
          {/* Question Recap */}
          <div className="flex items-center justify-between text-xs pb-2.5 border-b border-[#1F2937] text-slate-400">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium text-slate-300">Inquiry:</span>
              <span className="italic text-slate-200">&ldquo;{response.question}&rdquo;</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              Portfolio {response.portfolio_id.slice(0, 8)}...
            </span>
          </div>

          {/* AI Explanation Content */}
          <div className="text-sm text-slate-200 leading-relaxed space-y-3 font-normal">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Answer
            </div>
            {response.answer.split("\n\n").map((para, i) => (
              <p key={i} className="whitespace-pre-line text-slate-200">
                {para.trim()}
              </p>
            ))}
          </div>

          {/* Warnings Section (if present) */}
          {response.warnings && response.warnings.length > 0 && (
            <div className="pt-2">
              <div className="bg-amber-950/30 border border-amber-800/60 rounded-md p-3 text-xs text-amber-200/90 space-y-1">
                <div className="flex items-center gap-1.5 font-medium text-amber-300">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Data Advisories:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-amber-200/80 text-[11px]">
                  {response.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Based On: Metrics Used Indicator */}
          {response.metrics_used && response.metrics_used.length > 0 && (
            <div className="pt-3 border-t border-[#1F2937]">
              <div className="text-[11px] font-medium text-slate-400 mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                <span>Based on verified quantitative metrics:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {response.metrics_used.map((m, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center text-[11px] font-mono bg-[#161F2E] text-slate-300 border border-slate-700/60 px-2 py-0.5 rounded"
                  >
                    {METRIC_LABELS[m] || m.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Compliance Disclaimer */}
          <div className="pt-2 text-[10px] text-slate-500 italic">
            * AI Financial Analyst outputs are strictly grounded in deterministic portfolio analytics and are provided for educational and analytical purposes only. They do not constitute personalized financial, investment, tax, or trading advice.
          </div>
        </div>
      )}
    </section>
  );
}
