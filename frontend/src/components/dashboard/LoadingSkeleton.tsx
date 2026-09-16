"use client";

import React from "react";

export function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-label="Loading portfolio dashboard">
      {/* Header skeleton */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="h-4 w-32 bg-[#1F2937] rounded"></div>
          <div className="h-8 w-64 bg-[#374151] rounded"></div>
          <div className="h-3 w-48 bg-[#1F2937] rounded"></div>
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-48 bg-[#1F2937] rounded-lg"></div>
          <div className="h-10 w-24 bg-[#1F2937] rounded-lg"></div>
        </div>
      </div>

      {/* KPI Grid skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 space-y-3">
            <div className="h-3 w-20 bg-[#1F2937] rounded"></div>
            <div className="h-7 w-28 bg-[#374151] rounded"></div>
            <div className="h-3 w-16 bg-[#1F2937] rounded"></div>
          </div>
        ))}
      </div>

      {/* Performance chart skeleton */}
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 space-y-4">
        <div className="flex justify-between items-center">
          <div className="h-5 w-48 bg-[#374151] rounded"></div>
          <div className="h-8 w-32 bg-[#1F2937] rounded-lg"></div>
        </div>
        <div className="h-72 w-full bg-[#1F2937]/50 rounded-lg"></div>
      </div>

      {/* 2-column grid skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 space-y-4">
          <div className="h-5 w-36 bg-[#374151] rounded"></div>
          <div className="h-64 bg-[#1F2937]/50 rounded-lg"></div>
        </div>
        <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 space-y-4">
          <div className="h-5 w-36 bg-[#374151] rounded"></div>
          <div className="h-64 bg-[#1F2937]/50 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
}
