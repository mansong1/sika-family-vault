"use client";

import CreditScoreWidget from "@/components/CreditScoreWidget";
import Link from "next/link";

export default function CreditScorePage() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-800">
        <div className="max-w-2xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="p-1.5 -ml-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <svg
                className="w-5 h-5 text-slate-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </Link>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
              SusuScore™
            </h1>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-6 py-8">
        <div className="mb-8">
          <p className="text-sm text-slate-500 leading-relaxed">
            Your SusuScore™ is built from your savings group participation —
            on-time contributions, circle completion, and consistency. It's your
            financial reputation, earned one payment at a time.
          </p>
        </div>

        <CreditScoreWidget />

        {/* What affects your score */}
        <div className="mt-12 p-6 rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
            What Affects Your SusuScore™
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {[
              { emoji: "✅", text: "On-time contributions", positive: true },
              { emoji: "🔥", text: "Consistent savings streaks", positive: true },
              { emoji: "👥", text: "Multiple active circles", positive: true },
              { emoji: "📊", text: "Stable contribution amounts", positive: true },
              { emoji: "⚠️", text: "Late or missed payments", positive: false },
              { emoji: "🚫", text: "Circle defaults", positive: false },
            ].map((item) => (
              <div
                key={item.text}
                className="flex items-start gap-2"
              >
                <span className="text-sm">{item.emoji}</span>
                <span
                  className={`text-xs leading-relaxed ${
                    item.positive
                      ? "text-slate-600 dark:text-slate-400"
                      : "text-slate-500 dark:text-slate-500"
                  }`}
                >
                  {item.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
