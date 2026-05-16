const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  body?: any;
}

export async function apiFetch<T = unknown>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  register: (data: { email: string; phone_number: string; full_name: string; password: string }) =>
    apiFetch("/api/v1/auth/register", { method: "POST", body: data }),
  login: (data: { email: string; password: string }) =>
    apiFetch("/api/v1/auth/login", { method: "POST", body: data }),

  // Circles
  getCircles: () => apiFetch("/api/v1/circles"),
  createCircle: (data: { name: string; description?: string; contribution_amount: number; cycle_length_days: number; max_members: number; penalty_for_late?: number }) =>
    apiFetch("/api/v1/circles", { method: "POST", body: data }),
  getCircle: (id: string) => apiFetch(`/api/v1/circles/${id}`),
  joinCircle: (id: string) => apiFetch(`/api/v1/circles/${id}/join`, { method: "POST" }),
  makePayment: (circleId: string, data: { amount: number; provider: string; phone_number: string }) =>
    apiFetch(`/api/v1/circles/${circleId}/pay`, { method: "POST", body: { ...data, circle_id: circleId } }),
  getSchedule: (id: string) => apiFetch(`/api/v1/circles/${id}/schedule`),

  // Dashboard
  getDashboard: () => apiFetch("/api/v1/dashboard"),

  // Credit
  getCreditScore: () => apiFetch("/api/v1/credit-score"),

  // Legacy roundup (keep for dashboard endpoint)
  getRoundup: () => apiFetch("/api/v1/roundup"),
  createRoundup: (data: { round_to: number; active: boolean }) =>
    apiFetch("/api/v1/roundup", { method: "POST", body: { ...data, user_id: "" } }),

  // New Round-Up Engine
  roundUp: {
    createRule: (data: {
      circle_id: string;
      round_to?: number;
      multiplier?: number;
      floor_amount?: number;
      weekly_cap?: number;
      allocation_pct?: number;
    }) =>
      apiFetch("/round-up/rules", { method: "POST", body: { ...data, user_id: "" } }),

    getRules: () =>
      apiFetch<{ rules: unknown }>("/round-up/rules").then((d) => d.rules),

    updateRule: (ruleId: string, data: Record<string, unknown>) =>
      apiFetch(`/round-up/rules/${ruleId}`, { method: "PATCH", body: data }),

    deleteRule: (ruleId: string) =>
      apiFetch(`/round-up/rules/${ruleId}`, { method: "DELETE" }),

    getTransactions: (circleId?: string) =>
      apiFetch<{ transactions: unknown }>(`/round-up/transactions${circleId ? `?circle_id=${circleId}` : ""}`).then(
        (d) => d.transactions
      ),

    simulate: (purchaseAmount: number, circleId: string) =>
      apiFetch("/round-up/simulate", {
        method: "POST",
        body: { purchase_amount: purchaseAmount, circle_id: circleId },
      }),

    triggerSweep: (purchaseAmount: number, circleId: string) =>
      apiFetch("/round-up/sweep", {
        method: "POST",
        body: { purchase_amount: purchaseAmount, circle_id: circleId },
      }),

    getCircleStats: (circleId: string) =>
      apiFetch(`/round-up/circle-stats/${circleId}`),
  },
};
