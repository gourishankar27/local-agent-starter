import React, { useState, useEffect } from "react";
import { postJSON, getJSON } from "./api";

type EmailResult = {
  subject: string;
  snippet: string;
  summary_raw: string;
};

type ResumeResult = {
  profile: string;
  bullets: string[];
  cover_letter: string;
};

type LogEntry = {
  id: number;
  timestamp: string;
  event_type: string;
  meta: any;
  preview: string;
};

const App: React.FC = () => {
  const [tab, setTab] = useState<"agent" | "logs">("agent");

  return (
    <div className="app-root">
      <header style={{ marginBottom: 16 }}>
        <h1>Local Agent</h1>
        <nav style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setTab("agent")}
            style={{ padding: "6px 12px", fontWeight: tab === "agent" ? 700 : 400 }}
          >
            Agent
          </button>
          <button
            onClick={() => setTab("logs")}
            style={{ padding: "6px 12px", fontWeight: tab === "logs" ? 700 : 400 }}
          >
            Logs
          </button>
        </nav>
      </header>

      {tab === "agent" ? <AgentView /> : <LogsView />}
    </div>
  );
};

const AgentView: React.FC = () => {
  // Email state
  const [emailCount, setEmailCount] = useState("3");
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailResults, setEmailResults] = useState<EmailResult[]>([]);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Resume state
  const [jobText, setJobText] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeResult, setResumeResult] = useState<ResumeResult | null>(null);
  const [resumeError, setResumeError] = useState<string | null>(null);

  const summarizeEmails = async () => {
    setEmailLoading(true);
    setEmailError(null);
    setEmailResults([]);
    try {
      const count = parseInt(emailCount || "3", 10) || 3;
      const data = await postJSON("/email/summarize/", { count });
      setEmailResults(data.results || []);
    } catch (err: any) {
      setEmailError(err.message || String(err));
    } finally {
      setEmailLoading(false);
    }
  };

  const tailorResume = async () => {
    setResumeLoading(true);
    setResumeError(null);
    setResumeResult(null);
    try {
      const data = await postJSON("/resume/tailor/", {
        job_text: jobText,
        resume_text: resumeText
      });
      setResumeResult(data);
    } catch (err: any) {
      setResumeError(err.message || String(err));
    } finally {
      setResumeLoading(false);
    }
  };

  return (
    <>
      <div className="card">
        <h2>Summarize Recent Emails</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <label>
            Number of emails:{" "}
            <input
              type="number"
              min={1}
              max={20}
              value={emailCount}
              onChange={(e) => setEmailCount(e.target.value)}
              style={{ width: 60 }}
            />
          </label>
          <button onClick={summarizeEmails} disabled={emailLoading}>
            {emailLoading ? "Working..." : "Run"}
          </button>
        </div>
        {emailError && <div style={{ color: "red" }}>{emailError}</div>}
        {emailResults.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {emailResults.map((r, idx) => (
              <div
                key={idx}
                style={{ borderTop: "1px solid #ddd", paddingTop: 8, marginTop: 8 }}
              >
                <strong>Subject:</strong> {r.subject}
                <pre style={{ whiteSpace: "pre-wrap" }}>{r.summary_raw}</pre>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Tailor Resume for Job</h2>
        <div style={{ marginBottom: 8 }}>
          <label>Job Description:</label>
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste job description..."
          />
        </div>
        <div style={{ marginBottom: 8 }}>
          <label>Your Resume (plain text):</label>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your resume text..."
          />
        </div>
        <button onClick={tailorResume} disabled={resumeLoading}>
          {resumeLoading ? "Working..." : "Generate Tailored Profile & Cover Letter"}
        </button>
        {resumeError && <div style={{ color: "red", marginTop: 8 }}>{resumeError}</div>}
        {resumeResult && (
          <div style={{ marginTop: 12 }}>
            <h3>Profile</h3>
            <p>{resumeResult.profile}</p>

            <h3>Bullets</h3>
            <ul>
              {resumeResult.bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>

            <h3>Cover Letter</h3>
            <pre style={{ whiteSpace: "pre-wrap" }}>{resumeResult.cover_letter}</pre>
          </div>
        )}
      </div>
    </>
  );
};

const LogsView: React.FC = () => {
  const [password, setPassword] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // filters
  const [typeFilter, setTypeFilter] = useState("All");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selected, setSelected] = useState<LogEntry | null>(null);

  const unlockLogs = async () => {
    setLoading(true);
    setError(null);
    setLogs([]);
    setSelected(null);
    try {
      const data = await postJSON("/logs/unlock/", { password });
      setUnlocked(true);
      setLogs(data.logs || []);
    } catch (err: any) {
      setError(err.message || String(err));
      setUnlocked(false);
    } finally {
      setLoading(false);
    }
  };

  const refreshLogs = async () => {
    if (!unlocked) return;
    setLoading(true);
    setError(null);
    setSelected(null);
    const qs = new URLSearchParams();
    if (typeFilter && typeFilter !== "All") qs.set("type", typeFilter);
    if (startDate) qs.set("start", startDate);
    if (endDate) qs.set("end", endDate);

    try {
      const data = await getJSON(`/logs/${qs.toString() ? `?${qs.toString()}` : ""}`);
      setLogs(data.logs || []);
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (unlocked) {
      refreshLogs().catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, startDate, endDate]);

  const deleteLog = async (id: number) => {
    if (!window.confirm("Delete this log entry?")) return;
    setLoading(true);
    setError(null);
    try {
      const data = await postJSON("/logs/delete/", { id });
      setLogs(data.logs || []);
      setSelected(null);
    } catch (err: any) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="card">
        <h2>Unlock Logs</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Log password"
          />
          <button onClick={unlockLogs} disabled={loading || !password}>
            {loading ? "Working..." : "Unlock"}
          </button>
          {unlocked && <span>✅ Unlocked</span>}
        </div>
        <p style={{ marginTop: 8, fontSize: 13 }}>
          First time? Pick any password – it will be used to encrypt new logs. If logs already
          exist, you must use the same password you chose originally.
        </p>
        {error && <div style={{ color: "red" }}>{error}</div>}
      </div>

      <div className="card">
        <h2>History</h2>
        {!unlocked ? (
          <p>Unlock logs to view history.</p>
        ) : (
          <>
            <div
              style={{
                display: "flex",
                gap: 8,
                marginBottom: 8,
                alignItems: "center",
                flexWrap: "wrap"
              }}
            >
              <label>
                Type:&nbsp;
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <option value="All">All</option>
                  <option value="email_summary">email_summary</option>
                  <option value="resume_tailor">resume_tailor</option>
                </select>
              </label>
              <label>
                Start:&nbsp;
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </label>
              <label>
                End:&nbsp;
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </label>
              <button onClick={refreshLogs} disabled={loading}>
                Refresh
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "2fr 3fr", gap: 12 }}>
              <div
                style={{
                  maxHeight: 400,
                  overflow: "auto",
                  border: "1px solid #ddd",
                  borderRadius: 4
                }}
              >
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 4 }}>Time</th>
                      <th style={{ borderBottom: "1px solid #ddd", padding: 4 }}>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((l) => (
                      <tr
                        key={l.id}
                        onClick={() => setSelected(l)}
                        style={{
                          cursor: "pointer",
                          background:
                            selected && selected.id === l.id ? "#eef" : "transparent"
                        }}
                      >
                        <td style={{ borderBottom: "1px solid #eee", padding: 4 }}>
                          {l.timestamp}
                        </td>
                        <td style={{ borderBottom: "1px solid #eee", padding: 4 }}>
                          {l.event_type}
                        </td>
                      </tr>
                    ))}
                    {logs.length === 0 && (
                      <tr>
                        <td colSpan={2} style={{ padding: 4 }}>
                          No logs found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div
                style={{
                  border: "1px solid #ddd",
                  borderRadius: 4,
                  padding: 8,
                  minHeight: 200
                }}
              >
                {selected ? (
                  <>
                    <div style={{ marginBottom: 8 }}>
                      <strong>Time:</strong> {selected.timestamp}
                      <br />
                      <strong>Type:</strong> {selected.event_type}
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <strong>Meta:</strong>
                      <pre style={{ whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(selected.meta, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <strong>Preview:</strong>
                      <pre style={{ whiteSpace: "pre-wrap" }}>{selected.preview}</pre>
                    </div>
                    <button
                      style={{ marginTop: 8 }}
                      onClick={() => deleteLog(selected.id)}
                      disabled={loading}
                    >
                      Delete this log
                    </button>
                  </>
                ) : (
                  <p>Select a log on the left to see details.</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default App;
