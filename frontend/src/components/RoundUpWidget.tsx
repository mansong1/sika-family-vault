"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import Link from "next/link";

interface RoundUpRule {
  rule_id: string;
  circle_id: string;
  active: boolean;
  paused: boolean;
  round_to: number;
  multiplier: number;
  total_accumulated: number;
}

interface Circle {
  id: string;
  name: string;
}

export default function RoundUpWidget() {
  const [rules, setRules] = useState<RoundUpRule[]>([]);
  const [circles, setCircles] = useState<Circle[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCoinDrop, setShowCoinDrop] = useState(false);

  useEffect(() => {
    Promise.all([api.roundUp.getRules(), api.getCircles()])
      .then(([rulesData, circlesData]) => {
        setRules((rulesData as RoundUpRule[]) || []);
        setCircles((circlesData as Circle[]) || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Coin drop animation on mount
    const timer = setTimeout(() => setShowCoinDrop(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const totalAccumulated = rules.reduce((sum, r) => sum + r.total_accumulated, 0);
  const activeRules = rules.filter((r) => r.active && !r.paused);
  const hasRules = rules.length > 0;

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-sika-slate-200">
        <div className="skeleton h-4 w-32 mb-3 rounded" />
        <div className="skeleton h-8 w-24 mb-2 rounded" />
        <div className="skeleton h-3 w-40 rounded" />
      </div>
    );
  }

  if (!hasRules) {
    return (
      <Link href="/round-ups">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-5 shadow-sm border border-sika-slate-200 hover:border-sika-gold/30 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-sika-slate-100 flex items-center justify-center shrink-0">
              <svg
                className="w-5 h-5 text-sika-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <div className="text-sm font-medium text-sika-slate-700">
                Auto Round-Up
              </div>
              <div className="text-xs text-sika-slate-400">
                Set up spare change savings
              </div>
            </div>
            <svg
              className="w-4 h-4 text-sika-slate-300 ml-auto"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </motion.div>
      </Link>
    );
  }

  const circleName = (circleId: string) =>
    circles.find((c) => c.id === circleId)?.name || "Circle";

  return (
    <Link href="/round-ups">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl p-5 shadow-sm border border-sika-slate-200 hover:border-sika-gold/30 transition-colors cursor-pointer relative overflow-hidden"
      >
        {/* Coin drop animation */}
        {showCoinDrop && (
          <motion.div
            initial={{ y: -30, opacity: 0, scale: 0.5 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 15 }}
            className="absolute top-3 right-4 text-xl"
          >
            🪙
          </motion.div>
        )}

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-sika-slate-700">
              Auto Round-Up
            </span>
            {activeRules.length > 0 && (
              <span className="w-2 h-2 rounded-full bg-sika-success" />
            )}
          </div>
          <svg
            className="w-4 h-4 text-sika-slate-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="flex items-end gap-1 mb-1">
          <span className="text-xs text-sika-slate-400">GHS</span>
          <span className="font-display text-2xl text-sika-slate-900">
            {totalAccumulated.toFixed(2)}
          </span>
        </div>

        <div className="text-xs text-sika-slate-400">
          {activeRules.length > 0
            ? `${activeRules.length} active rule${activeRules.length > 1 ? "s" : ""} · ${rules.length} circle${rules.length > 1 ? "s" : ""}`
            : "Tap to configure"}
        </div>

        {/* Progress ring */}
        {totalAccumulated > 0 && (
          <div className="absolute bottom-3 right-4">
            <svg width="32" height="32" viewBox="0 0 32 32">
              <circle
                cx="16"
                cy="16"
                r="14"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="2"
              />
              <motion.circle
                cx="16"
                cy="16"
                r="14"
                fill="none"
                stroke="#D4A017"
                strokeWidth="2"
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 0.6 }}
                transition={{ duration: 1.5, delay: 0.5 }}
                style={{ rotate: -90, transformOrigin: "center" }}
                strokeDasharray="87.96"
              />
            </svg>
          </div>
        )}
      </motion.div>
    </Link>
  );
}
