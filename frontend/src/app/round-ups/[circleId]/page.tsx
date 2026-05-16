"use client";

import CircleRoundUp from "@/components/CircleRoundUp";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function CircleRoundUpsPage() {
  const params = useParams();
  const circleId = params.circleId as string;

  return (
    <div className="min-h-screen bg-sika-slate-50">
      <header className="bg-white border-b border-sika-slate-200 sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-6 py-4 flex items-center gap-3">
          <Link href="/round-ups" className="text-sika-slate-500 hover:text-sika-slate-700">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="font-display text-xl text-sika-slate-900">Circle Round-Ups</h1>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-8">
        <CircleRoundUp circleId={circleId} />
      </main>
    </div>
  );
}
