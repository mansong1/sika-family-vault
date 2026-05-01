"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-sika-slate-50 flex flex-col">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="flex-1 flex flex-col justify-center px-6 py-16 max-w-lg mx-auto w-full"
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="w-20 h-20 bg-sika-gold rounded-3xl flex items-center justify-center mb-8 mx-auto"
        >
          <span className="text-4xl">🪙</span>
        </motion.div>

        <motion.h1
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="font-display text-5xl text-sika-slate-900 text-center mb-4 leading-tight"
        >
          Sika Bank
        </motion.h1>

        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-lg text-sika-slate-500 text-center mb-12"
        >
          Digital Susu circles. Save together, grow together.
        </motion.p>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="space-y-3"
        >
          <Link
            href="/dashboard"
            className="block w-full bg-sika-gold text-white text-center font-semibold py-4 rounded-2xl text-lg hover:bg-sika-gold-dark transition-colors"
          >
            Get Started
          </Link>
          <Link
            href="/circles"
            className="block w-full bg-white text-sika-slate-700 text-center font-semibold py-4 rounded-2xl text-lg border border-sika-slate-200 hover:bg-sika-slate-50 transition-colors"
          >
            Explore Circles
          </Link>
        </motion.div>

        {/* Trust badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-12 flex items-center justify-center gap-6 text-xs text-sika-slate-400"
        >
          <span className="flex items-center gap-1">
            <span>🔒</span> Encrypted
          </span>
          <span className="flex items-center gap-1">
            <span>🛡️</span> Insured
          </span>
          <span className="flex items-center gap-1">
            <span>⚡</span> Instant
          </span>
        </motion.div>
      </motion.div>
    </div>
  );
}
