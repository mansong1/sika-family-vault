"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import Link from "next/link";
import { ChevronRight, Plus, Users } from "lucide-react";

interface Circle {
  id: string;
  name: string;
  description?: string;
  status: string;
  contribution_amount: number;
  member_count: number;
  max_members: number;
  total_collected: number;
  created_at: string;
}

export default function CirclesPage() {
  const [circles, setCircles] = useState<Circle[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCircles().then((c) => {
      setCircles(c);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-sika-slate-50">
        <div className="max-w-lg mx-auto px-6 py-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-28 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-sika-slate-50">
      <header className="bg-white border-b border-sika-slate-200 sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sika-slate-400">
              <ChevronRight className="rotate-180 w-5 h-5" />
            </Link>
            <h1 className="font-display text-xl text-sika-slate-900">My Circles</h1>
          </div>
          <Link
            href="/circles/new"
            className="w-10 h-10 bg-sika-gold rounded-full flex items-center justify-center text-white hover:bg-sika-gold-dark transition-colors"
          >
            <Plus className="w-5 h-5" />
          </Link>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-8">
        {circles.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">👥</div>
            <h2 className="font-display text-2xl text-sika-slate-900 mb-2">No circles yet</h2>
            <p className="text-sika-slate-500 mb-8">Create or join a Susu circle to start saving</p>
            <Link
              href="/circles/new"
              className="inline-block bg-sika-gold text-white font-semibold px-8 py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors"
            >
              Create Circle
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {circles.map((circle, i) => (
              <motion.div
                key={circle.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <Link
                  href={`/circles/${circle.id}`}
                  className="block bg-white rounded-2xl p-5 border border-sika-slate-200 hover:border-sika-gold/30 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-sika-slate-800">{circle.name}</h3>
                      {circle.description && (
                        <p className="text-sm text-sika-slate-500 mt-1">{circle.description}</p>
                      )}
                    </div>
                    <span className={`
                      text-xs px-2 py-1 rounded-full font-medium
                      ${circle.status === "active" ? "bg-sika-success/10 text-sika-success" : ""}
                      ${circle.status === "pending" ? "bg-sika-warning/10 text-sika-warning" : ""}
                      ${circle.status === "completed" ? "bg-sika-slate-100 text-sika-slate-500" : ""}
                    `}>
                      {circle.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-sm text-sika-slate-500">
                      <span className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        {circle.member_count}/{circle.max_members}
                      </span>
                      <span>GHS {circle.contribution_amount}/mo</span>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sika-slate-800">GHS {circle.total_collected.toLocaleString()}</div>
                      <div className="text-xs text-sika-slate-400"> collected</div>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
