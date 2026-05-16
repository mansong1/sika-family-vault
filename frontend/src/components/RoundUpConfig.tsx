"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";

interface Circle {
  id: string;
  name: string;
  contribution_amount: number;
}

interface Rule {
  rule_id: string;
  circle_id: string;
  active: boolean;
  paused: boolean;
  paused_until: string | null;
  round_to: number;
  multiplier: number;
  floor_amount: number;
  weekly_cap: number | null;
  allocation_pct: number;
  total_accumulated: number;
}

const ROUND_OPTIONS = [0.5, 1, 5, 10];
const MULTIPLIER_OPTIONS = [1, 2, 5];

export default function RoundUpConfig() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [circles, setCircles] = useState<Circle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCircle, setSelectedCircle] = useState("");
  const [roundTo, setRoundTo] = useState(1);
  const [multiplier, setMultiplier] = useState(1);
  const [floorAmount, setFloorAmount] = useState(0.10);
  const [weeklyCap, setWeeklyCap] = useState("");
  const [allocationPct, setAllocationPct] = useState(100);
  const [showNewRule, setShowNewRule] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.roundUp.getRules(),
      api.getCircles(),
    ])
      .then(([rulesData, circlesData]) => {
        setRules((rulesData as Rule[]) || []);
        setCircles((circlesData as Circle[]) || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleCreate = async () => {
    if (!selectedCircle) {
      setError("Select a circle");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await api.roundUp.createRule({
        circle_id: selectedCircle,
        round_to: roundTo,
        multiplier,
        floor_amount: floorAmount,
        weekly_cap: weeklyCap ? parseFloat(weeklyCap) : undefined,
        allocation_pct: allocationPct,
      });
      // Refresh
      const updated = await api.roundUp.getRules();
      setRules((updated as Rule[]) || []);
      setShowNewRule(false);
      resetForm();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create rule");
    }
    setSubmitting(false);
  };

  const handleToggle = async (rule: Rule) => {
    try {
      await api.roundUp.updateRule(rule.rule_id, { active: !rule.active });
      const updated = await api.roundUp.getRules();
      setRules((updated as Rule[]) || []);
    } catch {
      // silent fail
    }
  };

  const handlePause = async (rule: Rule) => {
    if (rule.paused) {
      await api.roundUp.updateRule(rule.rule_id, { paused_until: null });
    } else {
      // Pause for 7 days
      const future = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
      await api.roundUp.updateRule(rule.rule_id, { paused_until: future });
    }
    const updated = await api.roundUp.getRules();
    setRules((updated as Rule[]) || []);
  };

  const handleDelete = async (ruleId: string) => {
    await api.roundUp.deleteRule(ruleId);
    const updated = await api.roundUp.getRules();
    setRules((updated as Rule[]) || []);
  };

  const resetForm = () => {
    setSelectedCircle("");
    setRoundTo(1);
    setMultiplier(1);
    setFloorAmount(0.10);
    setWeeklyCap("");
    setAllocationPct(100);
  };

  const circleName = (id: string) => circles.find((c) => c.id === id)?.name || id;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-16 rounded-2xl" />
        <div className="skeleton h-16 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-lg text-sika-slate-900">Round-Up Rules</h2>
          <p className="text-sm text-sika-slate-500 mt-0.5">
            Spare change automatically flows to your Susu circles
          </p>
        </div>
        {!showNewRule && circles.length > 0 && (
          <button
            onClick={() => setShowNewRule(true)}
            className="text-sm font-medium text-sika-gold hover:text-sika-gold-dark transition-colors"
          >
            + Add Rule
          </button>
        )}
      </div>

      {/* New Rule Form */}
      {showNewRule && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="bg-white rounded-2xl p-5 shadow-sm border border-sika-gold/20 overflow-hidden"
        >
          <h3 className="font-medium text-sika-slate-800 mb-4">New Round-Up Rule</h3>

          {error && (
            <div className="mb-4 text-sm text-sika-danger bg-sika-danger/5 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {/* Circle Select */}
            <div>
              <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                Fund Circle
              </label>
              <select
                value={selectedCircle}
                onChange={(e) => setSelectedCircle(e.target.value)}
                className="w-full text-sm bg-sika-slate-50 border border-sika-slate-200 rounded-xl px-3 py-2.5 text-sika-slate-900 focus:outline-none focus:border-sika-gold focus:ring-1 focus:ring-sika-gold/30"
              >
                <option value="">Select a circle...</option>
                {circles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} (GHS {c.contribution_amount}/cycle)
                  </option>
                ))}
              </select>
            </div>

            {/* Round To */}
            <div>
              <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                Round to nearest
              </label>
              <div className="flex gap-2">
                {ROUND_OPTIONS.map((v) => (
                  <button
                    key={v}
                    onClick={() => setRoundTo(v)}
                    className={`flex-1 py-2 rounded-xl text-sm font-medium transition-colors ${
                      roundTo === v
                        ? "bg-sika-gold text-white"
                        : "bg-sika-slate-100 text-sika-slate-600 hover:bg-sika-slate-200"
                    }`}
                  >
                    GHS {v}
                  </button>
                ))}
              </div>
            </div>

            {/* Multiplier */}
            <div>
              <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                Multiplier
              </label>
              <div className="flex gap-2">
                {MULTIPLIER_OPTIONS.map((v) => (
                  <button
                    key={v}
                    onClick={() => setMultiplier(v)}
                    className={`flex-1 py-2 rounded-xl text-sm font-medium transition-colors ${
                      multiplier === v
                        ? "bg-sika-gold text-white"
                        : "bg-sika-slate-100 text-sika-slate-600 hover:bg-sika-slate-200"
                    }`}
                  >
                    {v}x
                  </button>
                ))}
              </div>
            </div>

            {/* Floor + Weekly Cap */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                  Floor amount (GHS)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={floorAmount}
                  onChange={(e) => setFloorAmount(parseFloat(e.target.value) || 0)}
                  className="w-full text-sm bg-sika-slate-50 border border-sika-slate-200 rounded-xl px-3 py-2.5 text-sika-slate-900 focus:outline-none focus:border-sika-gold focus:ring-1 focus:ring-sika-gold/30"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                  Weekly cap (GHS)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="None"
                  value={weeklyCap}
                  onChange={(e) => setWeeklyCap(e.target.value)}
                  className="w-full text-sm bg-sika-slate-50 border border-sika-slate-200 rounded-xl px-3 py-2.5 text-sika-slate-900 focus:outline-none focus:border-sika-gold focus:ring-1 focus:ring-sika-gold/30 placeholder-sika-slate-300"
                />
              </div>
            </div>

            {/* Allocation */}
            <div>
              <label className="block text-xs font-medium text-sika-slate-500 mb-1.5">
                Allocation: {allocationPct}%
              </label>
              <input
                type="range"
                min="1"
                max="100"
                value={allocationPct}
                onChange={(e) => setAllocationPct(parseInt(e.target.value))}
                className="w-full accent-sika-gold"
              />
              <div className="flex justify-between text-[10px] text-sika-slate-400 mt-0.5">
                <span>1%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => {
                  setShowNewRule(false);
                  resetForm();
                }}
                className="flex-1 py-2.5 text-sm font-medium text-sika-slate-500 bg-sika-slate-100 rounded-xl hover:bg-sika-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={submitting}
                className="flex-1 py-2.5 text-sm font-medium text-white bg-sika-gold rounded-xl hover:bg-sika-gold-dark transition-colors disabled:opacity-50"
              >
                {submitting ? "Creating..." : "Create Rule"}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Existing Rules */}
      {rules.length === 0 && !showNewRule && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-white rounded-2xl p-8 shadow-sm border border-sika-slate-200 text-center"
        >
          <div className="text-4xl mb-3">🪙</div>
          <h3 className="font-medium text-sika-slate-800 mb-1">No Round-Up Rules</h3>
          <p className="text-sm text-sika-slate-500 mb-4">
            Set up spare change savings for your Susu circles
          </p>
          {circles.length > 0 ? (
            <button
              onClick={() => setShowNewRule(true)}
              className="text-sm font-medium text-sika-gold hover:text-sika-gold-dark transition-colors"
            >
              Create your first rule
            </button>
          ) : (
            <p className="text-xs text-sika-slate-400">
              Create a Susu circle first to get started
            </p>
          )}
        </motion.div>
      )}

      {/* Rule Cards */}
      <div className="space-y-3">
        {rules.map((rule, i) => (
          <motion.div
            key={rule.rule_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`bg-white rounded-2xl p-4 shadow-sm border transition-colors ${
              rule.active && !rule.paused
                ? "border-sika-slate-200"
                : "border-sika-slate-100 bg-sika-slate-50/50"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sika-slate-800 text-sm">
                    {circleName(rule.circle_id)}
                  </span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                      rule.active && !rule.paused
                        ? "bg-sika-success/10 text-sika-success"
                        : rule.paused
                          ? "bg-sika-warning/10 text-sika-warning"
                          : "bg-sika-slate-200 text-sika-slate-500"
                    }`}
                  >
                    {rule.paused ? "Paused" : rule.active ? "Active" : "Off"}
                  </span>
                </div>
                <div className="text-xs text-sika-slate-400 mt-0.5">
                  GHS {rule.total_accumulated.toFixed(2)} accumulated
                </div>
              </div>

              {/* Toggle */}
              <button
                onClick={() => handleToggle(rule)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  rule.active ? "bg-sika-gold" : "bg-sika-slate-300"
                }`}
              >
                <motion.div
                  animate={{ x: rule.active ? 20 : 2 }}
                  className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-sm"
                />
              </button>
            </div>

            <div className="flex items-center gap-4 text-xs text-sika-slate-500">
              <span>Round to GHS {rule.round_to}</span>
              <span>·</span>
              <span>{rule.multiplier}x multiplier</span>
              {rule.floor_amount > 0 && (
                <>
                  <span>·</span>
                  <span>Min {rule.floor_amount}</span>
                </>
              )}
            </div>

            <div className="flex items-center gap-3 mt-3 pt-3 border-t border-sika-slate-100">
              <button
                onClick={() => handlePause(rule)}
                className="text-xs text-sika-slate-500 hover:text-sika-slate-700 transition-colors"
              >
                {rule.paused ? "▶ Resume" : "⏸ Pause"}
              </button>
              <span className="text-sika-slate-200">|</span>
              <button
                onClick={() => handleDelete(rule.rule_id)}
                className="text-xs text-sika-slate-400 hover:text-sika-danger transition-colors"
              >
                Delete
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
