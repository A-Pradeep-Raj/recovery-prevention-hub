import type {
  CaregiverAlert,
  CheckIn,
  CoPilotAnswer,
  CrisisEvent,
  RecoveryProfile,
  TriggerCrisisResponse,
  User,
} from "./types";

// Production (Cloud Run): browser calls the backend directly via an absolute
// URL baked in at build time. Local dev: relative "/api" path, proxied by
// Vite to localhost:8080 (see vite.config.ts).
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  listUsers: () => req<User[]>("/users"),
  createProfile: (payload: {
    user_id: string; triggers: string[]; coping_strategies: string[];
    support_contacts: string[]; sobriety_start_date?: string; notes?: string;
  }) => req<RecoveryProfile>("/profiles", { method: "POST", body: JSON.stringify(payload) }),
  getProfileByUser: (userId: string) => req<RecoveryProfile>(`/profiles/by-user/${userId}`),
  triggerCrisis: (userId: string, triggerMethod: "tap" | "voice", sharedContext?: string) =>
    req<TriggerCrisisResponse>("/crisis/trigger", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, trigger_method: triggerMethod, shared_context: sharedContext }),
    }),
  listCrisisEvents: () => req<CrisisEvent[]>("/crisis"),
  listAlerts: () => req<CaregiverAlert[]>("/crisis/alerts"),
  acknowledgeAlert: (alertId: string) =>
    req<CaregiverAlert>(`/crisis/alerts/${alertId}/acknowledge`, { method: "PATCH", body: JSON.stringify({}) }),
  createCheckin: (userId: string, type: string, intensity: number) =>
    req<CheckIn>("/checkins", { method: "POST", body: JSON.stringify({ user_id: userId, type, intensity }) }),
  listCheckins: () => req<CheckIn[]>("/checkins"),
  askCopilot: (userId: string, question: string, language = "en") =>
    req<CoPilotAnswer>("/copilot/ask", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, question, language }),
    }),
};
