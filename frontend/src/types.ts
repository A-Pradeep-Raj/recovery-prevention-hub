export interface User {
  id: string;
  name: string;
  email: string;
  role: "individual" | "caregiver";
  preferred_language: string;
  linked_user_ids: string[];
}

export interface RecoveryProfile {
  id: string;
  user_id: string;
  triggers: string[];
  coping_strategies: string[];
  support_contacts: string[];
  sobriety_start_date?: string | null;
  notes?: string | null;
}

export interface CrisisEvent {
  id: string;
  user_id: string;
  triggered_at: string;
  trigger_method: string;
  generated_script: string;
  grounded_fields: string[];
  caregiver_alert_id?: string | null;
  status: "open" | "resolved";
}

export interface CaregiverAlert {
  id: string;
  crisis_event_id: string;
  caregiver_id: string;
  context_summary: string;
  suggested_action: string;
  sent_at: string;
  acknowledged_at?: string | null;
  language_used: string;
}

export interface CheckIn {
  id: string;
  user_id: string;
  type: "craving" | "mood" | "sleep" | "stress";
  intensity: number;
  suggested_technique?: string | null;
  created_at: string;
}

export interface CoPilotAnswer {
  answer: string;
  source: string;
}

export interface TriggerCrisisResponse {
  event: CrisisEvent;
  caregiver_alert: CaregiverAlert | null;
}
