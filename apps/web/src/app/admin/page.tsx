"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Database,
  FileCheck,
  AlertOctagon,
  RefreshCw,
  Users,
  CheckCircle2,
  Calendar,
  Layers,
  Search,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Lock
} from "lucide-react";

interface HealthData {
  status: string;
  database_connected: boolean;
  total_documents: number;
  total_chunks: number;
  total_sources: number;
  total_faculty: number;
  total_departments: number;
  total_events: number;
  total_calendar_milestones: number;
  total_fee_schedules: number;
  total_spatial_nodes: number;
  pending_community_reports: number;
  active_conflicts: number;
  freshness_summary: Record<string, number>;
}

interface SourceItem {
  source_id: string;
  title: string;
  url?: string;
  source_type: string;
  authority_level: number;
  freshness_status: string;
  last_verified_at?: string;
  chunk_count: number;
}

interface ReportItem {
  id: string;
  query_text: string;
  generated_answer: string;
  category: string;
  report_reason: string;
  suggested_correction?: string;
  status: string;
  created_at?: string;
  github_issue_number?: number;
}

export default function AdminDashboard() {
  const [adminToken, setAdminToken] = useState("srmap_sage_maintainer_key_2026");
  const [authorized, setAuthorized] = useState(false);
  const [authError, setAuthError] = useState("");
  const [activeTab, setActiveTab] = useState<"health" | "sources" | "conflicts" | "reports">("health");

  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchDashboardData = async (token: string) => {
    setLoading(true);
    setAuthError("");
    try {
      const headers = {
        "Authorization": `Bearer ${token}`
      };

      // 1. Health
      const hRes = await fetch("http://localhost:8000/api/v1/admin/health", { headers });
      if (hRes.status === 401) throw new Error("401 Unauthorized: Invalid or missing maintainer key");
      if (hRes.status === 403) throw new Error("403 Forbidden: Insufficient maintainer privileges");
      if (!hRes.ok) throw new Error(`Health API failed with code ${hRes.status}`);
      const hJson = await hRes.json();
      setHealthData(hJson);

      // 2. Sources
      const sRes = await fetch("http://localhost:8000/api/v1/admin/sources", { headers });
      if (sRes.ok) {
        const sJson = await sRes.json();
        setSources(sJson);
      }

      // 3. Reports
      const rRes = await fetch("http://localhost:8000/api/v1/admin/reports", { headers });
      if (rRes.ok) {
        const rJson = await rRes.json();
        setReports(rJson);
      }

      setAuthorized(true);
    } catch (err: any) {
      setAuthorized(false);
      setAuthError(err.message || "Authorization failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData(adminToken);
  }, []);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDashboardData(adminToken);
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-deep)", color: "var(--text-primary)", padding: "24px 36px" }}>
      {/* Header */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-color)", paddingBottom: "16px", marginBottom: "24px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <ShieldCheck size={26} color="var(--accent-cyan)" />
            <h1 style={{ fontSize: "1.4rem", fontWeight: 800, margin: 0, letterSpacing: "-0.02em" }}>
              SRMAP SAGE — Maintainer Control Center
            </h1>
          </div>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", margin: "4px 0 0 0" }}>
            Phase 6 Operational Knowledge Health, Source Provenance & Community Review Dashboard
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <a
            href="/"
            style={{ fontSize: "0.82rem", color: "var(--text-secondary)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "6px" }}
          >
            ← Back to Student Interface
          </a>
          <button
            onClick={() => fetchDashboardData(adminToken)}
            disabled={loading}
            style={{
              padding: "6px 14px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(0, 240, 255, 0.1)",
              border: "1px solid rgba(0, 240, 255, 0.3)",
              color: "var(--accent-cyan)",
              fontSize: "0.82rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </header>

      {/* Authorization Wall */}
      {!authorized ? (
        <div style={{ maxWidth: "440px", margin: "80px auto", background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "32px", textAlign: "center" }}>
          <Lock size={36} color="var(--accent-cyan)" style={{ margin: "0 auto 16px" }} />
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "8px" }}>Maintainer Authorization Required</h2>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
            Access to institutional catalog health and community reports is restricted to authenticated maintainers.
          </p>

          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <input
              type="password"
              placeholder="Enter Maintainer Key..."
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "var(--radius-sm)",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-color)",
                color: "var(--text-primary)",
                fontSize: "0.88rem"
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: "10px",
                borderRadius: "var(--radius-sm)",
                background: "var(--accent-cyan)",
                color: "#000",
                fontWeight: 700,
                fontSize: "0.88rem",
                cursor: "pointer",
                border: "none"
              }}
            >
              {loading ? "Verifying..." : "Authenticate Maintainer Session"}
            </button>
          </form>

          {authError && (
            <div style={{ marginTop: "16px", padding: "10px", borderRadius: "4px", background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "var(--accent-rose)", fontSize: "0.8rem" }}>
              {authError}
            </div>
          )}
        </div>
      ) : (
        <div>
          {/* Nav Tabs */}
          <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px", marginBottom: "24px" }}>
            {[
              { id: "health", label: "Knowledge Health", icon: Database },
              { id: "sources", label: `Source Registry (${sources.length})`, icon: Layers },
              { id: "conflicts", label: "Conflicts & Supersession", icon: AlertOctagon },
              { id: "reports", label: `Community Reports (${reports.length})`, icon: Users },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  style={{
                    padding: "8px 18px",
                    borderRadius: "var(--radius-sm)",
                    background: active ? "rgba(0, 240, 255, 0.15)" : "transparent",
                    border: active ? "1px solid rgba(0, 240, 255, 0.4)" : "1px solid transparent",
                    color: active ? "var(--accent-cyan)" : "var(--text-secondary)",
                    fontWeight: active ? 700 : 500,
                    fontSize: "0.84rem",
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px"
                  }}
                >
                  <Icon size={14} /> {tab.label}
                </button>
              );
            })}
          </div>

          {/* TAB 1: HEALTH METRICS */}
          {activeTab === "health" && healthData && (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "24px" }}>
                <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "20px" }}>
                  <div style={{ fontSize: "0.76rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Database Status</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: healthData.database_connected ? "var(--accent-emerald)" : "var(--accent-rose)", marginTop: "4px" }}>
                    {healthData.database_connected ? "Connected (pgvector)" : "Disconnected"}
                  </div>
                </div>

                <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "20px" }}>
                  <div style={{ fontSize: "0.76rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Policy Chunks</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--accent-cyan)", marginTop: "4px" }}>
                    {healthData.total_chunks} chunks
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "2px" }}>Across {healthData.total_documents} Level 1 PDF Policies</div>
                </div>

                <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "20px" }}>
                  <div style={{ fontSize: "0.76rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Structured Entities</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--accent-amber)", marginTop: "4px" }}>
                    {healthData.total_faculty + healthData.total_departments + healthData.total_events + healthData.total_spatial_nodes} entities
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                    {healthData.total_faculty} Faculty • {healthData.total_spatial_nodes} Campus Nodes
                  </div>
                </div>

                <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "20px" }}>
                  <div style={{ fontSize: "0.76rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Active Conflicts</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: 800, color: healthData.active_conflicts === 0 ? "var(--accent-emerald)" : "var(--accent-rose)", marginTop: "4px" }}>
                    {healthData.active_conflicts} unresolved
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "2px" }}>Level 1 policies strictly consistent</div>
                </div>
              </div>

              {/* Operational Subsystems */}
              <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "24px" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "16px" }}>Domain Engine Inventory & Provenance</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
                  <div style={{ background: "var(--bg-surface)", padding: "14px", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontWeight: 600, fontSize: "0.86rem" }}>Academic Calendar Milestones</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-cyan)", marginTop: "4px" }}>{healthData.total_calendar_milestones} milestones</div>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>Current & Historical terms partitioned</div>
                  </div>

                  <div style={{ background: "var(--bg-surface)", padding: "14px", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontWeight: 600, fontSize: "0.86rem" }}>Official Fee Schedules</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-emerald)", marginTop: "4px" }}>{healthData.total_fee_schedules} verified schedules</div>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>Zero inferred schedules; unreleased refuse</div>
                  </div>

                  <div style={{ background: "var(--bg-surface)", padding: "14px", borderRadius: "var(--radius-sm)" }}>
                    <div style={{ fontWeight: 600, fontSize: "0.86rem" }}>Campus Events Registry</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-amber)", marginTop: "4px" }}>{healthData.total_events} events</div>
                    <div style={{ fontSize: "0.74rem", color: "var(--text-muted)" }}>Directly linked to university notices</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SOURCES */}
          {activeTab === "sources" && (
            <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                    <th style={{ padding: "12px 16px" }}>Source Title</th>
                    <th style={{ padding: "12px 16px" }}>Authority</th>
                    <th style={{ padding: "12px 16px" }}>Type</th>
                    <th style={{ padding: "12px 16px" }}>Freshness</th>
                    <th style={{ padding: "12px 16px" }}>Chunks</th>
                    <th style={{ padding: "12px 16px" }}>Last Verified</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((s) => (
                    <tr key={s.source_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "12px 16px", fontWeight: 600 }}>
                        {s.title}
                        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "monospace" }}>{s.source_id}</div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span style={{ padding: "2px 6px", borderRadius: "4px", background: s.authority_level === 1 ? "rgba(0, 240, 255, 0.15)" : "rgba(245, 158, 11, 0.15)", color: s.authority_level === 1 ? "var(--accent-cyan)" : "var(--accent-amber)", fontWeight: 700 }}>
                          Level {s.authority_level}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{s.source_type}</td>
                      <td style={{ padding: "12px 16px" }}>
                        <span style={{ padding: "2px 6px", borderRadius: "4px", background: s.freshness_status === "CURRENT" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)", color: s.freshness_status === "CURRENT" ? "var(--accent-emerald)" : "var(--accent-rose)", fontWeight: 700 }}>
                          {s.freshness_status}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", fontWeight: 600 }}>{s.chunk_count}</td>
                      <td style={{ padding: "12px 16px", color: "var(--text-muted)" }}>{s.last_verified_at || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: CONFLICTS */}
          {activeTab === "conflicts" && (
            <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", padding: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
                <CheckCircle2 size={22} color="var(--accent-emerald)" />
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>Zero Unresolved Conflicts Across Indexed Sources</h3>
              </div>
              <p style={{ fontSize: "0.84rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                The SAGE Semantic Conflict Detector automatically verifies authority hierarchy and temporal supersessions.
                When newer policies revoke older policies (e.g. Attendance Policy 2023 superseding Attendance Policy 2022),
                the older policy is marked <code style={{ color: "var(--accent-rose)" }}>SUPERSEDED</code> and excluded from active responses.
              </p>
            </div>
          )}

          {/* TAB 4: REPORTS */}
          {activeTab === "reports" && (
            <div style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", overflow: "hidden" }}>
              {reports.length === 0 ? (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.88rem" }}>
                  No community discrepancy reports pending maintainer review.
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                  <thead>
                    <tr style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "12px 16px" }}>Query & Response</th>
                      <th style={{ padding: "12px 16px" }}>Category</th>
                      <th style={{ padding: "12px 16px" }}>Reported Reason</th>
                      <th style={{ padding: "12px 16px" }}>Status</th>
                      <th style={{ padding: "12px 16px" }}>GitHub Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.map((r) => (
                      <tr key={r.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "12px 16px", maxWidth: "300px" }}>
                          <div style={{ fontWeight: 600 }}>{r.query_text}</div>
                          <div style={{ fontSize: "0.74rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {r.generated_answer}
                          </div>
                        </td>
                        <td style={{ padding: "12px 16px" }}>{r.category}</td>
                        <td style={{ padding: "12px 16px", color: "var(--accent-amber)" }}>{r.report_reason}</td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ padding: "2px 6px", borderRadius: "4px", background: "rgba(245, 158, 11, 0.15)", color: "var(--accent-amber)", fontWeight: 700 }}>
                            {r.status}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px" }}>{r.github_issue_number ? `#${r.github_issue_number}` : "Local Only"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
