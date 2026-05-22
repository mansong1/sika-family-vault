"use client";

import { useEffect, useState } from "react";
import { getCreditScore, CreditScoreData } from "@/lib/credit-score-api";

const TIER_COLORS: Record<string, { stroke: string; bg: string; text: string }> = {
  Excellent: { stroke: "#D4AF37", bg: "rgba(212,175,55,0.12)", text: "text-amber-600" },
  "Very Good": { stroke: "#22C55E", bg: "rgba(34,197,94,0.12)", text: "text-emerald-600" },
  Good: { stroke: "#3B82F6", bg: "rgba(59,130,246,0.12)", text: "text-blue-600" },
  Fair: { stroke: "#F59E0B", bg: "rgba(245,158,11,0.12)", text: "text-amber-500" },
  "Needs Improvement": { stroke: "#EF4444", bg: "rgba(239,68,68,0.12)", text: "text-red-500" },
  default: { stroke: "#6B7280", bg: "rgba(107,114,128,0.12)", text: "text-slate-500" },
};

function CircularGauge({
  score,
  tier,
  trend,
}: {
  score: number;
  tier: string;
  trend: string;
}) {
  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const progress = (score - 300) / 550; // normalize to 0–1
  const strokeDashoffset = circumference * (1 - progress);
  const colors = TIER_COLORS[tier] || TIER_COLORS.default;

  const trendIcon = trend === "up" ? "↗" : trend === "down" ? "↘" : "→";
  const trendColor = trend === "up" ? "text-emerald-500" : trend === "down" ? "text-red-400" : "text-slate-400";

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: 180, height: 180 }}>
        {/* Background ring */}
        <svg
          className="transform -rotate-90"
          width="180"
          height="180"
          viewBox="0 0 180 180"
        >
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="none"
            stroke="rgba(0,0,0,0.06)"
            strokeWidth="8"
          />
          {/* Progress ring */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            fill="none"
            stroke={colors.stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums">
            {score}
          </span>
          <span className={`text-xs font-medium mt-0.5 ${trendColor}`}>
            {trendIcon}{" "}
            {trend === "up" ? "Improving" : trend === "down" ? "Needs attention" : "Stable"}
          </span>
        </div>
      </div>

      {/* Tier badge */}
      <span
        className="mt-3 px-3 py-1 rounded-full text-xs font-semibold tracking-wide"
        style={{ backgroundColor: colors.bg, color: colors.stroke }}
      >
        {tier}
      </span>
    </div>
  );
}

function ScoreFactorBar({ factor }: { factor: CreditScoreData["factors"][0] }) {
  const pct = Math.round(factor.normalized * 100);
  const width = `${Math.max(4, pct)}%`;

  return (
    <div className="mb-4 last:mb-0">
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {factor.name}
        </span>
        <span className="text-xs text-slate-500 tabular-nums">{pct}%</span>
      </div>
      <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width,
            backgroundColor: pct >= 70 ? "#22C55E" : pct >= 40 ? "#F59E0B" : "#EF4444",
          }}
        />
      </div>
      <p className="text-xs text-slate-400 mt-1">{factor.description}</p>
    </div>
  );
}

function ScoreHistory({ history }: { history: { date: string; score: number }[] }) {
  if (!history.length) return null;

  const minScore = Math.min(...history.map((h) => h.score)) - 20;
  const maxScore = Math.max(...history.map((h) => h.score)) + 20;
  const range = maxScore - minScore || 1;
  const width = 100 / (history.length - 1 || 1);

  const points = history
    .map((h, i) => {
      const x = i * width;
      const y = 100 - ((h.score - minScore) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="w-full">
      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
        Score History
      </h4>
      <div className="relative h-32">
        <svg
          className="w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((y) => (
            <line
              key={y}
              x1="0"
              y1={y}
              x2="100"
              y2={y}
              stroke="rgba(0,0,0,0.06)"
              strokeWidth="0.5"
            />
          ))}
          {/* Trend line */}
          <polyline
            points={points}
            fill="none"
            stroke="#D4AF37"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Start dot */}
          <circle
            cx={history[0] ? "0" : "0"}
            cy={history[0] ? `${100 - ((history[0].score - minScore) / range) * 100}` : "50"}
            r="2"
            fill="#D4AF37"
          />
          {/* End dot */}
          {history.length > 1 && (
            <circle
              cx="100"
              cy={`${100 - ((history[history.length - 1].score - minScore) / range) * 100}`}
              r="2.5"
              fill="#D4AF37"
            />
          )}
        </svg>
      </div>
    </div>
  );
}

function ImprovementTips({ tips }: { tips: string[] }) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
        How to Improve
      </h4>
      {tips.map((tip, i) => (
        <div
          key={i}
          className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/30"
        >
          <span className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
            {tip}
          </span>
        </div>
      ))}
    </div>
  );
}

function SkeletonWidget() {
  return (
    <div className="flex flex-col items-center animate-pulse">
      <div className="w-[180px] h-[180px] rounded-full bg-slate-100 dark:bg-slate-800" />
      <div className="mt-3 w-24 h-6 rounded-full bg-slate-100 dark:bg-slate-800" />
      <div className="mt-6 w-full space-y-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i}>
            <div className="flex justify-between mb-1">
              <div className="w-32 h-4 rounded bg-slate-100 dark:bg-slate-800" />
              <div className="w-8 h-4 rounded bg-slate-100 dark:bg-slate-800" />
            </div>
            <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-900 text-white dark:bg-white dark:text-slate-900 hover:opacity-90 transition-opacity"
      >
        Try Again
      </button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-20 h-20 rounded-full bg-slate-50 dark:bg-slate-800/50 flex items-center justify-center mb-5">
        <svg
          className="w-10 h-10 text-slate-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-2">
        No Credit Score Yet
      </h3>
      <p className="text-sm text-slate-500 max-w-xs leading-relaxed">
        Start a Susu circle and make consistent contributions to build your
        SusuScore™. Your savings discipline becomes your credit history.
      </p>
    </div>
  );
}

export default function CreditScoreWidget() {
  const [data, setData] = useState<CreditScoreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScore = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getCreditScore();
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load credit score");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScore();
  }, []);

  if (loading) return <SkeletonWidget />;
  if (error) return <ErrorState message={error} onRetry={fetchScore} />;
  if (!data || data.score === 0) return <EmptyState />;

  return (
    <div className="space-y-8">
      {/* Main Gauge */}
      <CircularGauge score={data.score} tier={data.tier} trend={data.trend} />

      {/* Score Factors */}
      <div>
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
          Score Factors
        </h4>
        {data.factors.map((factor) => (
          <ScoreFactorBar key={factor.name} factor={factor} />
        ))}
      </div>

      {/* Score History */}
      <ScoreHistory
        history={
          data.last_calculated
            ? [
                {
                  date: data.last_calculated,
                  score: data.score,
                },
              ]
            : []
        }
      />

      {/* Improvement Tips */}
      {data.improvement_tips.length > 0 && (
        <ImprovementTips tips={data.improvement_tips} />
      )}
    </div>
  );
}
