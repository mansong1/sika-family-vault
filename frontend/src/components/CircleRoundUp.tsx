"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";

interface LeaderboardEntry {
  user_id: string;
  total: number;
  sweeps: number;
}

interface RecentSweep {
  id: string;
  user_id: string;
  spare_change: number;
  purchase_amount: number;
  multiplier: number;
  swept_at: string;
}

export default function CircleRoundUp({ circleId }: { circleId: string }) {
  const [stats, setStats] = useState<{
    circle_name: string;
    total_spare_change: number;
    total_sweeps: number;
    member_leaderboard: LeaderboardEntry[];
    recent_sweeps: RecentSweep[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.roundUp
      .getCircleStats(circleId)
      .then((data) => {
        setStats(data as {
          circle_name: string;
          total_spare_change: number;
          total_sweeps: number;
          member_leaderboard: LeaderboardEntry[];
          recent_sweeps: RecentSweep[];
        });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [circleId]);

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-GH", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-24 rounded-2xl" />
        <div className="skeleton h-40 rounded-2xl" />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-8">
        <div className="text-3xl mb-2">📊</div>
        <p className="text-sm text-sika-slate-500">Could not load stats</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-sika-slate-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-sika-gold/10 flex items-center justify-center">
            <span className="text-lg">🪙</span>
          </div>
          <div>
            <div className="font-display text-lg text-sika-slate-900">
              {stats.circle_name || "Circle"}
            </div>
            <div className="text-xs text-sika-slate-400">
              Spare Change Contributions
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-sika-slate-400 mb-1">Total Spare Change</div>
            <div className="font-display text-2xl text-sika-slate-900">
              GHS {stats.total_spare_change.toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-xs text-sika-slate-400 mb-1">Total Sweeps</div>
            <div className="font-display text-2xl text-sika-slate-900">
              {stats.total_sweeps}
            </div>
          </div>
        </div>
      </div>

      {/* Member Leaderboard */}
      <div>
        <h3 className="text-sm font-semibold text-sika-slate-700 mb-3">
          Member Leaderboard
        </h3>
        {stats.member_leaderboard.length === 0 ? (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-sika-slate-200 text-center">
            <p className="text-sm text-sika-slate-400">No contributions yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {stats.member_leaderboard.map((entry, i) => (
              <motion.div
                key={entry.user_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-white rounded-xl p-3 shadow-sm border border-sika-slate-200 flex items-center gap-3"
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${
                    i === 0
                      ? "bg-sika-gold text-white"
                      : i === 1
                        ? "bg-sika-slate-300 text-white"
                        : i === 2
                          ? "bg-amber-100 text-amber-700"
                          : "bg-sika-slate-100 text-sika-slate-500"
                  }`}
                >
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-sika-slate-800 truncate">
                    Member {entry.user_id.slice(0, 6)}
                  </div>
                  <div className="text-xs text-sika-slate-400">
                    {entry.sweeps} sweep{entry.sweeps > 1 ? "s" : ""}
                  </div>
                </div>
                <div className="text-sm font-semibold text-sika-slate-900">
                  GHS {entry.total.toFixed(2)}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Sweeps */}
      <div>
        <h3 className="text-sm font-semibold text-sika-slate-700 mb-3">
          Recent Sweeps
        </h3>
        {stats.recent_sweeps.length === 0 ? (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-sika-slate-200 text-center">
            <p className="text-sm text-sika-slate-400">
              Sweeps will appear here
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {stats.recent_sweeps.map((sweep) => (
              <div
                key={sweep.id}
                className="bg-white rounded-xl p-3 shadow-sm border border-sika-slate-200 flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-medium text-sika-slate-700">
                    Purchase: GHS {sweep.purchase_amount.toFixed(2)}
                  </div>
                  <div className="text-[10px] text-sika-slate-400">
                    {formatTime(sweep.swept_at)}
                    {sweep.multiplier > 1 && ` · ${sweep.multiplier}x`}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-sika-success">
                    +GHS {sweep.spare_change.toFixed(2)}
                  </div>
                  <div className="text-[10px] text-sika-slate-400">spare change</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
