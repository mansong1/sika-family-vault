"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import RoundUpWidget from "@/components/RoundUpWidget";

interface DashboardData {
  user_id: string;
  credit_score: { score: number; rating: string };
  circles: { active: number; pending: number; total: number };
  total_saved: number;
  roundup_accumulated: number;
  upcoming_payments: { circle_name: string; amount: number; due_in_days: number }[];
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard().then((d) => {
      setData(d as DashboardData);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (!data) return <EmptyDashboard />;

  return (
    <div className="min-h-screen bg-sika-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-sika-slate-200 sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="font-display text-xl text-sika-slate-900">Sika Bank</h1>
          <div className="text-sm text-sika-slate-500">Dashboard</div>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-8 space-y-8">
        {/* Credit Score Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-sika-slate-200"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-sika-slate-500">Credit Score</span>
            <span className="text-xs bg-sika-gold/10 text-sika-gold-dark px-2 py-1 rounded-full">
              {data.credit_score.rating}
            </span>
          </div>
          <div className="flex items-end gap-2">
            <span className="font-display text-5xl text-sika-slate-900">
              {data.credit_score.score}
            </span>
            <span className="text-sm text-sika-slate-400 mb-2">/ 850</span>
          </div>
          <div className="mt-4 h-2 bg-sika-slate-100 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(data.credit_score.score / 850) * 100}%` }}
              transition={{ duration: 1, delay: 0.3 }}
              className="h-full bg-sika-gold rounded-full"
            />
          </div>
        </motion.div>

        {/* Round-Up Widget */}
        <RoundUpWidget />

        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl p-5 shadow-sm border border-sika-slate-200"
          >
            <div className="text-sm text-sika-slate-500 mb-1">Total Saved</div>
            <div className="font-display text-2xl text-sika-slate-900">
              GHS {data.total_saved.toLocaleString()}
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-5 shadow-sm border border-sika-slate-200"
          >
            <div className="text-sm text-sika-slate-500 mb-1">Active Circles</div>
            <div className="font-display text-2xl text-sika-slate-900">
              {data.circles.active}
            </div>
          </motion.div>
        </div>

        {/* Upcoming Payments */}
        {data.upcoming_payments.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-sika-slate-700 mb-4">Upcoming Payments</h2>
            <div className="space-y-3">
              {data.upcoming_payments.map((p, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="bg-white rounded-xl p-4 border border-sika-slate-200 flex items-center justify-between"
                >
                  <div>
                    <div className="font-medium text-sika-slate-800">{p.circle_name}</div>
                    <div className="text-sm text-sika-slate-500">
                      Due in {p.due_in_days} days
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-sika-slate-900">GHS {p.amount}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <Link
          href="/circles"
          className="block w-full bg-sika-gold text-white text-center font-semibold py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors"
        >
          View My Circles
        </Link>
      </main>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-sika-slate-50">
      <div className="max-w-lg mx-auto px-6 py-8 space-y-8">
        <div className="skeleton h-40 rounded-2xl" />
        <div className="grid grid-cols-2 gap-4">
          <div className="skeleton h-28 rounded-2xl" />
          <div className="skeleton h-28 rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

function EmptyDashboard() {
  return (
    <div className="min-h-screen bg-sika-slate-50 flex items-center justify-center px-6">
      <div className="text-center">
        <div className="text-6xl mb-4">🏦</div>
        <h2 className="font-display text-2xl text-sika-slate-900 mb-2">Welcome to Sika Bank</h2>
        <p className="text-sika-slate-500 mb-8">Start your first Susu circle today</p>
        <Link
          href="/circles/new"
          className="inline-block bg-sika-gold text-white font-semibold px-8 py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors"
        >
          Create Circle
        </Link>
      </div>
    </div>
  );
}
