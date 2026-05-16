"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronLeft, Users, Calendar, Wallet, Shield, CheckCircle } from "lucide-react";

interface CircleDetail {
  id: string;
  name: string;
  description?: string;
  status: string;
  contribution_amount: number;
  cycle_length_days: number;
  max_members: number;
  penalty_for_late: number;
  total_collected: number;
  insurance_pool_balance: number;
  members: { user_id: string; role: string; position?: number; has_paid_current_cycle: boolean; joined_at: string }[];
  cycles: { cycle_number: number; start_date: string; end_date: string; payout_to?: string; total_collected: number; status: string }[];
  current_cycle?: number;
  created_at: string;
}

export default function CircleDetailPage() {
  const params = useParams();
  const circleId = params.id as string;
  const [circle, setCircle] = useState<CircleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPayment, setShowPayment] = useState(false);

  useEffect(() => {
    api.getCircle(circleId).then((c) => {
      setCircle(c as CircleDetail);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [circleId]);

  if (loading) return <CircleDetailSkeleton />;
  if (!circle) return <div>Circle not found</div>;

  const currentCycle = circle.cycles[circle.cycles.length - 1];
  const membersSorted = [...circle.members].sort((a, b) => (a.position ?? 999) - (b.position ?? 999));

  return (
    <div className="min-h-screen bg-sika-slate-50">
      <header className="bg-white border-b border-sika-slate-200">
        <div className="max-w-lg mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/circles" className="text-sika-slate-400">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="font-display text-xl text-sika-slate-900">{circle.name}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              circle.status === "active" ? "bg-sika-success/10 text-sika-success" : "bg-sika-warning/10 text-sika-warning"
            }`}>
              {circle.status}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-8 space-y-6">
        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 gap-4"
        >
          <div className="bg-white rounded-2xl p-5 border border-sika-slate-200">
            <div className="flex items-center gap-2 text-sika-slate-500 mb-2">
              <Wallet className="w-4 h-4" />
              <span className="text-sm">Collected</span>
            </div>
            <div className="font-display text-2xl text-sika-slate-900">GHS {circle.total_collected.toLocaleString()}</div>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-sika-slate-200">
            <div className="flex items-center gap-2 text-sika-slate-500 mb-2">
              <Shield className="w-4 h-4" />
              <span className="text-sm">Insurance</span>
            </div>
            <div className="font-display text-2xl text-sika-slate-900">GHS {circle.insurance_pool_balance.toLocaleString()}</div>
          </div>
        </motion.div>

        {/* Members */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl p-6 border border-sika-slate-200"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-sika-slate-800 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Members ({circle.members.length}/{circle.max_members})
            </h2>
          </div>
          <div className="space-y-3">
            {membersSorted.map((member, i) => (
              <div key={member.user_id} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-sika-gold/20 flex items-center justify-center text-sm font-medium text-sika-gold-dark">
                    {i + 1}
                  </div>
                  <div>
                    <div className="font-medium text-sm text-sika-slate-800">
                      {member.role === "admin" ? "👑 " : ""}
                      {member.user_id.slice(0, 8)}...
                    </div>
                    <div className="text-xs text-sika-slate-400">{member.role}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {member.has_paid_current_cycle && (
                    <span className="text-sika-success">
                      <CheckCircle className="w-5 h-5" />
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Current Cycle */}
        {currentCycle && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-6 border border-sika-slate-200"
          >
            <div className="flex items-center gap-2 text-sika-slate-500 mb-4">
              <Calendar className="w-5 h-5" />
              <span className="font-semibold text-sika-slate-800">Cycle {currentCycle.cycle_number}</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-sika-slate-500">Started</span>
                <span className="text-sika-slate-700">{new Date(currentCycle.start_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-sika-slate-500">Ends</span>
                <span className="text-sika-slate-700">{new Date(currentCycle.end_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-sika-slate-500">Payout to</span>
                <span className="text-sika-slate-700 font-medium">{currentCycle.payout_to?.slice(0, 8)}...</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Payment Button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          onClick={() => setShowPayment(true)}
          className="w-full bg-sika-gold text-white font-semibold py-4 rounded-2xl hover:bg-sika-gold-dark transition-colors"
        >
          Pay GHS {circle.contribution_amount}
        </motion.button>

        {/* Payment Modal */}
        {showPayment && (
          <PaymentModal
            circleId={circle.id}
            amount={circle.contribution_amount}
            onClose={() => setShowPayment(false)}
            onSuccess={() => {
              setShowPayment(false);
              api.getCircle(circleId).then((c) => setCircle(c as CircleDetail));
            }}
          />
        )}
      </main>
    </div>
  );
}

function PaymentModal({ circleId, amount, onClose, onSuccess }: {
  circleId: string; amount: number; onClose: () => void; onSuccess: () => void;
}) {
  const [provider, setProvider] = useState("mtn_momo");
  const [phone, setPhone] = useState("");
  const [paying, setPaying] = useState(false);

  const handlePay = async () => {
    setPaying(true);
    try {
      await api.makePayment(circleId, { amount, provider, phone_number: phone });
      onSuccess();
    } catch {
      alert("Payment failed");
      setPaying(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="bg-white rounded-t-3xl sm:rounded-3xl p-6 w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-display text-xl text-sika-slate-900 mb-6">Pay Contribution</h3>
        <div className="space-y-4 mb-6">
          <div className="text-center py-4">
            <div className="text-sm text-sika-slate-500">Amount</div>
            <div className="font-display text-4xl text-sika-slate-900">GHS {amount}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">Provider</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: "mtn_momo", label: "MTN MoMo", color: "bg-yellow-400" },
                { id: "vodafone_cash", label: "Vodafone", color: "bg-red-500" },
                { id: "airteltigo", label: "AirtelTigo", color: "bg-blue-500" },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={`py-3 px-2 rounded-xl text-sm font-medium transition-all ${
                    provider === p.id
                      ? "bg-sika-gold text-white ring-2 ring-sika-gold/30"
                      : "bg-sika-slate-100 text-sika-slate-600"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-sika-slate-700 mb-2">Phone Number</label>
            <input
              type="tel"
              placeholder="+233501234567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-sika-slate-200 focus:border-sika-gold focus:ring-2 focus:ring-sika-gold/20 outline-none bg-white"
            />
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 rounded-xl bg-sika-slate-100 text-sika-slate-700 font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handlePay}
            disabled={paying || !phone}
            className="flex-1 py-3 rounded-xl bg-sika-gold text-white font-medium disabled:opacity-50"
          >
            {paying ? "Processing..." : "Pay Now"}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function CircleDetailSkeleton() {
  return (
    <div className="min-h-screen bg-sika-slate-50">
      <div className="max-w-lg mx-auto px-6 py-8 space-y-6">
        <div className="skeleton h-20 rounded-2xl" />
        <div className="grid grid-cols-2 gap-4">
          <div className="skeleton h-28 rounded-2xl" />
          <div className="skeleton h-28 rounded-2xl" />
        </div>
        <div className="skeleton h-48 rounded-2xl" />
      </div>
    </div>
  );
}
