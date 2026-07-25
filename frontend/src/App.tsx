import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { CoPilotAnswer, RecoveryProfile, TriggerCrisisResponse, User } from "./types";

function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  useEffect(() => {
    api.listUsers().then(setUsers);
  }, []);
  return users;
}

export default function App() {
  const [tab, setTab] = useState<"crisis" | "profile" | "copilot" | "caregiver">("crisis");
  const users = useUsers();
  const individuals = useMemo(() => users.filter((u) => u.role === "individual"), [users]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");

  useEffect(() => {
    if (!selectedUserId && individuals.length > 0) setSelectedUserId(individuals[0].id);
  }, [individuals, selectedUserId]);

  const individual = useMemo(() => individuals.find((u) => u.id === selectedUserId) ?? individuals[0], [individuals, selectedUserId]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <div className="brand-logo" aria-hidden="true">🛟</div>
            <div>
              <h1 className="brand-title">Recovery &amp; Prevention Hub</h1>
              <p className="brand-tagline">Support when cognitive load is highest — zero typing, always grounded.</p>
            </div>
          </div>
          {individuals.length > 0 && (
            <label className="user-switcher">
              <span>Demo user:</span>
              <select
                className="input"
                value={individual?.id ?? ""}
                onChange={(e) => setSelectedUserId(e.target.value)}
                aria-label="Select demo user"
              >
                {individuals.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({u.preferred_language.toUpperCase()})
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </header>

      <main className="container">
        <div className="tabs" role="tablist" aria-label="Views">
          <button role="tab" aria-selected={tab === "crisis"} className={`tab ${tab === "crisis" ? "active" : ""}`} onClick={() => setTab("crisis")}>
            Crisis Mode
          </button>
          <button role="tab" aria-selected={tab === "profile"} className={`tab ${tab === "profile" ? "active" : ""}`} onClick={() => setTab("profile")}>
            Safety Plan
          </button>
          <button role="tab" aria-selected={tab === "copilot"} className={`tab ${tab === "copilot" ? "active" : ""}`} onClick={() => setTab("copilot")}>
            Recovery Co-Pilot
          </button>
          <button role="tab" aria-selected={tab === "caregiver"} className={`tab ${tab === "caregiver" ? "active" : ""}`} onClick={() => setTab("caregiver")}>
            Caregiver Dashboard
          </button>
        </div>

        {tab === "crisis" && <CrisisMode key={individual?.id} userId={individual?.id} />}
        {tab === "profile" && <SafetyPlan key={individual?.id} userId={individual?.id} />}
        {tab === "copilot" && <CoPilot key={individual?.id} userId={individual?.id} />}
        {tab === "caregiver" && <CaregiverDashboard />}
      </main>
    </div>
  );
}

/** Zero-typing Crisis Mode (spec.md Section 3.1) — one tap, no forms. */
function CrisisMode({ userId }: { userId?: string }) {
  const [result, setResult] = useState<TriggerCrisisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function trigger(method: "tap" | "voice") {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await api.triggerCrisis(userId, method));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to trigger crisis mode.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-labelledby="crisis-heading">
      <h2 id="crisis-heading" className="section-title">Crisis Mode</h2>
      <p className="section-sub">Zero typing. One tap. A grounded, personalized script — generated live.</p>

      <div className="crisis-panel">
        <button className="crisis-btn" onClick={() => trigger("tap")} disabled={loading || !userId}>
          {loading ? "Generating…" : "🆘 I need help now"}
        </button>
        <p className="crisis-hint">If you are in immediate danger, call your local emergency number or a crisis line now.</p>
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}

      {result && (
        <div className="card crisis-result">
          <h3 style={{ marginTop: 0 }}>Your grounding script</h3>
          <p className="script-text">{result.event.generated_script}</p>
          <div className="grounded-trace">
            Grounded in: {result.event.grounded_fields.length > 0 ? result.event.grounded_fields.join(", ") : "generic fallback (limited profile data)"}
          </div>
          {result.caregiver_alert && (
            <div className="alert-box">
              <strong>Caregiver alerted.</strong> Suggested action for them: {result.caregiver_alert.suggested_action}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

/** Safety Plan editor grounds every AI response (spec.md Section 3.3). */
function SafetyPlan({ userId }: { userId?: string }) {
  const [profile, setProfile] = useState<RecoveryProfile | null>(null);
  const [triggers, setTriggers] = useState("");
  const [coping, setCoping] = useState("");
  const [contacts, setContacts] = useState("");
  const [saving, setSaving] = useState(false);
  const [checkinResult, setCheckinResult] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    api.getProfileByUser(userId).then(setProfile).catch(() => setProfile(null));
  }, [userId]);

  async function save() {
    if (!userId) return;
    setSaving(true);
    try {
      const p = await api.createProfile({
        user_id: userId,
        triggers: triggers.split(",").map((s) => s.trim()).filter(Boolean),
        coping_strategies: coping.split(",").map((s) => s.trim()).filter(Boolean),
        support_contacts: contacts.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setProfile(p);
    } finally {
      setSaving(false);
    }
  }

  async function checkIn(intensity: number) {
    if (!userId) return;
    const c = await api.createCheckin(userId, "craving", intensity);
    setCheckinResult(c.suggested_technique ?? null);
  }

  return (
    <section aria-labelledby="plan-heading">
      <h2 id="plan-heading" className="section-title">Safety Plan</h2>
      <p className="section-sub">Everything the AI generates for you is grounded in this plan — never invented.</p>

      <div className="card">
        <label className="form-field">
          <span>Known triggers (comma-separated)</span>
          <input className="input" value={triggers} onChange={(e) => setTriggers(e.target.value)} placeholder="stress at work, Friday nights" />
        </label>
        <label className="form-field">
          <span>Coping strategies that have worked before</span>
          <input className="input" value={coping} onChange={(e) => setCoping(e.target.value)} placeholder="call my sponsor, go for a run" />
        </label>
        <label className="form-field">
          <span>Support contacts</span>
          <input className="input" value={contacts} onChange={(e) => setContacts(e.target.value)} placeholder="Sam Lee, crisis line 988" />
        </label>
        <button className="btn" onClick={save} disabled={saving || !userId}>{saving ? "Saving…" : "Save Safety Plan"}</button>
      </div>

      {profile && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Current Plan</h3>
          <p><strong>Triggers:</strong> {profile.triggers.join(", ") || "none logged"}</p>
          <p><strong>Coping strategies:</strong> {profile.coping_strategies.join(", ") || "none logged"}</p>
          <p><strong>Support contacts:</strong> {profile.support_contacts.join(", ") || "none logged"}</p>
        </div>
      )}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Craving Check-In</h3>
        <p className="section-sub" style={{ marginBottom: 12 }}>Tap your current craving intensity — no typing.</p>
        <div className="intensity-row">
          {[2, 5, 8, 10].map((i) => (
            <button key={i} className="btn-ghost" onClick={() => checkIn(i)} disabled={!userId}>{i}/10</button>
          ))}
        </div>
        {checkinResult && <p className="answer-box" style={{ marginTop: 12 }}>Suggested technique: <strong>{checkinResult}</strong></p>}
      </div>
    </section>
  );
}

/** Recovery Co-Pilot chatbot — grounded Q&A with anti-hallucination guardrail (spec.md Section 3.5). */
function CoPilot({ userId }: { userId?: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<CoPilotAnswer | null>(null);
  const [asking, setAsking] = useState(false);

  async function ask() {
    if (!userId || !question.trim()) return;
    setAsking(true);
    try {
      setAnswer(await api.askCopilot(userId, question));
    } finally {
      setAsking(false);
    }
  }

  return (
    <section aria-labelledby="copilot-heading">
      <h2 id="copilot-heading" className="section-title">Recovery Co-Pilot</h2>
      <p className="section-sub">Ask anything about recovery, coping, or your Safety Plan.</p>

      <div className="card">
        <div className="chat-row">
          <input className="input" value={question} onChange={(e) => setQuestion(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && ask()} placeholder="e.g. What are my known triggers?" />
          <button className="btn" onClick={ask} disabled={asking}>{asking ? "Asking…" : "Ask"}</button>
        </div>
        {answer && (
          <div className="answer-box">
            <p style={{ margin: 0 }}>{answer.answer}</p>
            {answer.source && <blockquote>Source: "{answer.source}"</blockquote>}
          </div>
        )}
      </div>
    </section>
  );
}

/** Caregiver Dashboard: real-time alerts + suggested actions (spec.md Section 3.4). */
function CaregiverDashboard() {
  const [alerts, setAlerts] = useState<Awaited<ReturnType<typeof api.listAlerts>>>([]);

  const load = () => api.listAlerts().then(setAlerts);
  useEffect(() => { load(); }, []);

  return (
    <section aria-labelledby="caregiver-heading">
      <h2 id="caregiver-heading" className="section-title">Caregiver Dashboard</h2>
      <p className="section-sub">Real-time alerts with context and a suggested next action.</p>

      {alerts.length === 0 && <p className="empty">No alerts yet.</p>}

      {alerts.map((a) => (
        <div key={a.id} className="card">
          <p className="item-desc">{a.context_summary}</p>
          <p><strong>Suggested action:</strong> {a.suggested_action}</p>
          <div className="item-footer">
            <span className="badge pending_ack">{a.acknowledged_at ? "✅ Acknowledged" : "⏳ Awaiting acknowledgment"}</span>
            {!a.acknowledged_at && (
              <button className="btn-ghost" onClick={() => api.acknowledgeAlert(a.id).then(load)}>Acknowledge</button>
            )}
          </div>
        </div>
      ))}
    </section>
  );
}
