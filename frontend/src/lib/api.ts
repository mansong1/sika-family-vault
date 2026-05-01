const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  body?: any;
}

async function apiFetch(endpoint: string, options: RequestOptions = {}) {
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
  getCreditScore: () => apiFetch("/api/v1/credit-score"),
  getRoundup: () => apiFetch("/api/v1/roundup"),
  createRoundup: (data: { round_to: number; active: boolean }) =>
    apiFetch("/api/v1/roundup", { method: "POST", body: { ...data, user_id: "" } }),
};
