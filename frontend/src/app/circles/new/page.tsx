"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Loader2 } from "lucide-react";

export default function CreateCircle() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    contribution_amount: "",
    cycle_length_days: "30",
    max_members: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.createCircle({
        name: formData.name,
        description: formData.description || undefined,
        contribution_amount: parseFloat(formData.contribution_amount),
        cycle_length_days: parseInt(formData.cycle_length_days),
        max_members: parseInt(formData.max_members),
      });
      router.push("/circles");
    } catch (error) {
      alert("Failed to create circle");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-sika-slate-50">
      <header className="bg-white border-b border-sika-slate-200">
        <div className="max-w-lg mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/circles" className="text-sika-slate-400">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-display text-xl text-sika-slate-900">Create Circle</h1>
        </div>
      </header>

      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-lg mx-auto px-6 py-8"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">
              Circle Name
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Family Susu"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none transition-colors bg-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">
              Description
            </label>
            <input
              type="text"
              placeholder="What are you saving for?"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none transition-colors bg-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">
              Monthly Contribution (GHS)
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sika-slate-400">GHS</span>
              <input
                type="number"
                required
                min="10"
                placeholder="100"
                value={formData.contribution_amount}
                onChange={(e) => setFormData({ ...formData, contribution_amount: e.target.value })}
                className="w-full pl-14 pr-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none transition-colors bg-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">
              Cycle Length
            </label>
            <select
              value={formData.cycle_length_days}
              onChange={(e) => setFormData({ ...formData, cycle_length_days: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none transition-colors bg-white"
            >
              <option value="7">Weekly</option>
              <option value="14">Bi-weekly</option>
              <option value="30">Monthly</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">
              Max Members
            </label>
            <input
              type="number"
              required
              min="2"
              max="50"
              placeholder="5"
              value={formData.max_members}
              onChange={(e) => setFormData({ ...formData, max_members: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none transition-colors bg-white"
            />
            <p className="text-xs text-sika-slate-400 mt-2">
              Total payout per cycle: GHS {parseFloat(formData.contribution_amount || "0") * parseInt(formData.max_members || "0") || 0}
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-sika-gold text-white font-semibold py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
            Create Circle
          </button>
        </form>
      </motion.main>
    </div>
  );
}
