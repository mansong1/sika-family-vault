// SusuScore™ API client for the Credit Score Linkage feature

export interface ScoreFactor {
  name: string;
  normalized: number;
  weight: number;
  contribution: number;
  description: string;
}

export interface CreditScoreData {
  score: number;
  tier: string;
  trend: "up" | "down" | "stable";
  factors: ScoreFactor[];
  improvement_tips: string[];
  circles_completed: number;
  on_time_payments: number;
  late_payments: number;
  defaulted_circles: number;
  last_updated: string;
  last_calculated: string;
}

export interface ScoreHistoryPoint {
  date: string;
  score: number;
}

export interface ScoreHistory {
  current_score: number;
  history: ScoreHistoryPoint[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} — ${await res.text()}`);
  }
  return res.json();
}

export async function getCreditScore(): Promise<CreditScoreData> {
  return fetchApi<CreditScoreData>("/credit-score");
}

export async function getCreditScoreHistory(): Promise<ScoreHistory> {
  return fetchApi<ScoreHistory>("/credit-score/history");
}
