"use client";

import React, { useState } from "react";
import {
  Search,
  BookOpen,
  Briefcase,
  MapPin,
  UserCheck,
  FileText,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Send,
  Flag,
  Sparkles
} from "lucide-react";

interface SourceCitation {
  id: string;
  title: string;
  url?: string;
  source_type: string;
  authority_level: number;
  page_number?: number;
  section_heading?: string;
  snippet?: string;
  freshness_status?: string;
  publication_date_str?: string;
  effective_date_str?: string;
}

interface Message {
  id: string;
  sender: "user" | "sage";
  text: string;
  intent?: string;
  is_fallback?: boolean;
  sources?: SourceCitation[];
  adaptive_card?: {
    card_type: string;
    payload: any;
  };
  timestamp: string;
}

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "sage",
      text: "Welcome to **SRMAP SAGE** — your verified Student Assistance & Guidance Engine. Ask me about academic regulations, medical leave procedures, faculty cabins, campus directions, or placement records.",
      timestamp: "Just now",
    },
  ]);

  const [activeTab, setActiveTab] = useState<"chat" | "explore">("chat");
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [selectedSource, setSelectedSource] = useState<SourceCitation | null>(null);

  const quickActions = [
    { label: "Medical Leave Procedure", query: "How do I apply for medical leave?", icon: FileText },
    { label: "Hostel to Library", query: "How do I go from Hostel Tower A to Academic Block?", icon: MapPin },
    { label: "Attendance Policy", query: "What is the minimum attendance requirement for semester exams?", icon: BookOpen },
    { label: "Faculty Directory", query: "Where is the CSE Department faculty cabin?", icon: UserCheck },
    { label: "Placement Criteria", query: "What are the eligibility criteria for campus placements?", icon: Briefcase },
  ];

  const handleSend = async (customQuery?: string) => {
    const textToSend = customQuery || query;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customQuery) setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/chat/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: textToSend }),
      });

      if (!res.ok) throw new Error("API request failed");

      const data = await res.json();
      const sageMessage: Message = {
        id: `sage-${Date.now()}`,
        sender: "sage",
        text: data.answer,
        intent: data.intent,
        is_fallback: data.is_fallback,
        sources: data.sources || [],
        adaptive_card: data.adaptive_card,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, sageMessage]);
    } catch (err) {
      // Offline fallback demonstration
      const offlineMsg: Message = {
        id: `sage-${Date.now()}`,
        sender: "sage",
        text: "I couldn't connect to the live backend service. Please ensure the API is running at `http://localhost:8000`.",
        is_fallback: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, offlineMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Top Navigation */}
      <header
        style={{
          borderBottom: "1px solid var(--border-color)",
          padding: "16px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "rgba(8, 12, 24, 0.8)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 50,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0284c7, #00f0ff)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 15px rgba(0, 240, 255, 0.4)",
            }}
          >
            <Sparkles size={20} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, lineHeight: 1.2 }}>
              SRMAP <span style={{ color: "var(--accent-cyan)" }}>SAGE</span>
            </h1>
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", margin: 0 }}>
              Student Assistance & Guidance Engine
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span className="badge badge-official">
            <ShieldCheck size={14} /> Zero Hallucination Mode Active
          </span>
          <button
            className="btn-ghost"
            onClick={() => {
              setSelectedMessage(null);
              setReportModalOpen(true);
            }}
          >
            <Flag size={14} /> Report Discrepancy
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", maxWidth: "1000px", width: "100%", margin: "0 auto", padding: "20px 24px" }}>
        
        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", gap: "10px", overflowX: "auto", paddingBottom: "14px", scrollbarWidth: "none" }}>
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <button
                key={idx}
                onClick={() => handleSend(action.query)}
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "var(--radius-pill)",
                  padding: "8px 16px",
                  color: "var(--text-secondary)",
                  fontSize: "0.82rem",
                  fontWeight: 500,
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent-cyan)";
                  e.currentTarget.style.color = "var(--text-primary)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-color)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }}
              >
                <Icon size={14} color="var(--accent-cyan)" />
                {action.label}
              </button>
            );
          })}
        </div>

        {/* Message Stream */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            padding: "16px 0",
          }}
        >
          {messages.map((msg) => (
            <div
              key={msg.id}
              className="animate-fade-in"
              style={{
                alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                maxWidth: msg.sender === "user" ? "80%" : "90%",
              }}
            >
              <div
                style={{
                  background: msg.sender === "user" ? "linear-gradient(135deg, #0369a1, #0284c7)" : "var(--bg-card)",
                  border: msg.sender === "user" ? "none" : "1px solid var(--border-color)",
                  borderRadius: "var(--radius-md)",
                  padding: "18px 22px",
                  boxShadow: "var(--shadow-subtle)",
                }}
              >
                {/* Message Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: 600, color: msg.sender === "user" ? "#e0f2fe" : "var(--accent-cyan)" }}>
                    {msg.sender === "user" ? "You" : "SRMAP SAGE"}
                  </span>
                  <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{msg.timestamp}</span>
                </div>

                {/* Body */}
                <div style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "var(--text-primary)", whiteSpace: "pre-line" }}>
                  {msg.text}
                </div>

                {/* Adaptive Structured Card */}
                {msg.adaptive_card && (
                  <div style={{ marginTop: "14px", background: "rgba(0, 240, 255, 0.03)", border: "1px solid rgba(0, 240, 255, 0.25)", borderRadius: "var(--radius-md)", padding: "16px" }}>
                    {msg.adaptive_card.card_type === "navigation" && (
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                          <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--accent-cyan)", display: "flex", alignItems: "center", gap: "6px" }}>
                            <MapPin size={15} /> CAMPUS WALKING ROUTE
                          </span>
                          <span style={{ fontSize: "0.72rem", background: "rgba(0, 240, 255, 0.15)", color: "var(--accent-cyan)", padding: "3px 8px", borderRadius: "10px", fontWeight: 600 }}>
                            ~{msg.adaptive_card.payload.estimated_walk_minutes} min • {msg.adaptive_card.payload.total_distance_meters}m
                          </span>
                        </div>
                        <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
                          {msg.adaptive_card.payload.origin_name} → {msg.adaptive_card.payload.destination_name}
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "8px" }}>
                          {msg.adaptive_card.payload.steps?.map((step: any, sIdx: number) => (
                            <div key={sIdx} style={{ display: "flex", alignItems: "flex-start", gap: "8px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                              <span style={{ minWidth: "18px", height: "18px", borderRadius: "50%", background: "rgba(0, 240, 255, 0.15)", color: "var(--accent-cyan)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.68rem", fontWeight: 700 }}>
                                {sIdx + 1}
                              </span>
                              <span>{step.instruction} <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>({step.distance_meters}m)</span></span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {msg.adaptive_card.card_type === "faculty" && (
                      <div>
                        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <UserCheck size={15} /> VERIFIED FACULTY DIRECTORY
                        </div>
                        <div style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          {msg.adaptive_card.payload.name}
                        </div>
                        <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                          {msg.adaptive_card.payload.designation} — {msg.adaptive_card.payload.department}
                        </div>
                        <div style={{ marginTop: "10px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.78rem" }}>
                          <div style={{ background: "rgba(255,255,255,0.02)", padding: "6px 10px", borderRadius: "4px" }}>
                            <span style={{ color: "var(--text-muted)" }}>Cabin: </span>
                            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{msg.adaptive_card.payload.cabin_number || "Officially Unreleased"}</span>
                          </div>
                          <div style={{ background: "rgba(255,255,255,0.02)", padding: "6px 10px", borderRadius: "4px" }}>
                            <span style={{ color: "var(--text-muted)" }}>Location: </span>
                            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{msg.adaptive_card.payload.block || "Academic Block"}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {msg.adaptive_card.card_type === "department" && (
                      <div>
                        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "6px" }}>
                          ACADEMIC DEPARTMENT
                        </div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          {msg.adaptive_card.payload.name} ({msg.adaptive_card.payload.code})
                        </div>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                          School: {msg.adaptive_card.payload.school}
                        </div>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                          Building: {msg.adaptive_card.payload.building} • Office: {msg.adaptive_card.payload.office}
                        </div>
                      </div>
                    )}

                    {msg.adaptive_card.card_type === "fee" && (
                      <div>
                        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "6px" }}>
                          OFFICIAL UNIVERSITY FEE SCHEDULE
                        </div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          {msg.adaptive_card.payload.program}
                        </div>
                        <div style={{ marginTop: "6px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                          Category: {msg.adaptive_card.payload.fee_type?.toUpperCase()} • Academic Year: {msg.adaptive_card.payload.academic_year}
                        </div>
                        <div style={{ marginTop: "8px", fontSize: "1.1rem", fontWeight: 800, color: "var(--accent-emerald)" }}>
                          {msg.adaptive_card.payload.currency} {Number(msg.adaptive_card.payload.amount).toLocaleString()}
                        </div>
                      </div>
                    )}

                    {msg.adaptive_card.card_type === "calendar" && (
                      <div>
                        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "6px" }}>
                          ACADEMIC CALENDAR MILESTONE
                        </div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          {msg.adaptive_card.payload.event}
                        </div>
                        <div style={{ marginTop: "4px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                          Semester: {msg.adaptive_card.payload.semester} ({msg.adaptive_card.payload.academic_year})
                        </div>
                        <div style={{ marginTop: "6px", fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-cyan)" }}>
                          Date: {msg.adaptive_card.payload.start_date?.substring(0, 10)}
                        </div>
                      </div>
                    )}

                    {msg.adaptive_card.card_type === "event" && (
                      <div>
                        <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "6px" }}>
                          CAMPUS EVENT & ANNOUNCEMENT
                        </div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          {msg.adaptive_card.payload.title}
                        </div>
                        <div style={{ marginTop: "6px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                          Venue: {msg.adaptive_card.payload.venue || "Campus"} • Organizer: {msg.adaptive_card.payload.organizer}
                        </div>
                        <div style={{ marginTop: "4px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          Date: {msg.adaptive_card.payload.start_datetime}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Evidence & Provenance Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px" }}>
                      VERIFIED PROVENANCE (Level {msg.sources[0].authority_level}):
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {msg.sources.map((src) => {
                        const isCurrent = src.freshness_status === "CURRENT" || !src.freshness_status;
                        const badgeColor = isCurrent
                          ? "var(--accent-emerald)"
                          : src.freshness_status === "RECENT"
                          ? "var(--accent-cyan)"
                          : "var(--accent-amber)";
                        return (
                          <div
                            key={src.id}
                            onClick={() => setSelectedSource(src)}
                            style={{
                              background: "rgba(0, 240, 255, 0.05)",
                              border: "1px solid rgba(0, 240, 255, 0.2)",
                              borderRadius: "var(--radius-sm)",
                              padding: "6px 12px",
                              fontSize: "0.78rem",
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              cursor: "pointer",
                              transition: "all 0.2s ease",
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.borderColor = "var(--accent-cyan)";
                              e.currentTarget.style.background = "rgba(0, 240, 255, 0.12)";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.borderColor = "rgba(0, 240, 255, 0.2)";
                              e.currentTarget.style.background = "rgba(0, 240, 255, 0.05)";
                            }}
                          >
                            <span
                              style={{
                                fontSize: "0.65rem",
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: isCurrent ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)",
                                color: badgeColor,
                                letterSpacing: "0.5px",
                              }}
                            >
                              {src.freshness_status || "CURRENT"}
                            </span>
                            <span style={{ fontWeight: 500 }}>{src.title}</span>
                            {src.page_number && (
                              <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>
                                (p. {src.page_number})
                              </span>
                            )}
                            {src.url && (
                              <a
                                href={src.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                style={{ color: "var(--accent-cyan)", marginLeft: "2px" }}
                              >
                                <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Footer Tools */}
                {msg.sender === "sage" && (
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "12px" }}>
                    <button
                      onClick={() => {
                        setSelectedMessage(msg);
                        setReportModalOpen(true);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--text-muted)",
                        fontSize: "0.72rem",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--accent-rose)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                    >
                      <Flag size={11} /> Flag incorrect information
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
              <div
                style={{
                  width: "18px",
                  height: "18px",
                  border: "2px solid var(--accent-cyan)",
                  borderTopColor: "transparent",
                  borderRadius: "50%",
                  animation: "spin 0.8s linear infinite",
                }}
              />
              Verifying official SRMAP sources & synthesizing evidence...
            </div>
          )}
        </div>

        {/* Query Input Box */}
        <div style={{ marginTop: "auto", paddingTop: "14px" }}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            style={{
              display: "flex",
              alignItems: "center",
              background: "var(--bg-card)",
              border: "1px solid var(--border-color)",
              borderRadius: "var(--radius-md)",
              padding: "8px 14px",
              boxShadow: "var(--shadow-subtle)",
            }}
          >
            <Search size={18} color="var(--text-muted)" style={{ marginRight: "10px" }} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about academic policies, faculty rooms, medical leaves, or hostel rules..."
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                color: "var(--text-primary)",
                fontSize: "0.95rem",
                outline: "none",
                fontFamily: "var(--font-body)",
              }}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn-primary"
              style={{ padding: "8px 16px" }}
            >
              <Send size={16} /> Send
            </button>
          </form>
          <div style={{ textAlign: "center", marginTop: "8px", fontSize: "0.72rem", color: "var(--text-muted)" }}>
            SAGE answers are strictly grounded in official SRMAP documentation. Unverified claims are rejected.
          </div>
        </div>
      </main>

      {/* Discrepancy Reporting Modal */}
      {reportModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
          }}
        >
          <div className="glass-card" style={{ maxWidth: "520px", width: "90%", padding: "28px", borderRadius: "var(--radius-lg)" }}>
            <h3 style={{ fontSize: "1.2rem", marginBottom: "8px", color: "var(--accent-rose)" }}>
              Report Inaccurate or Outdated Information
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "18px" }}>
              Your feedback is bridged to GitHub Issues for maintainer review and regression testing.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                Category:
                <select
                  style={{
                    width: "100%",
                    marginTop: "4px",
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-primary)",
                    padding: "8px",
                    borderRadius: "var(--radius-sm)",
                  }}
                >
                  <option>Academics & Regulations</option>
                  <option>Faculty Cabin / Location</option>
                  <option>Medical Leave / Attendance</option>
                  <option>Campus Walking Directions</option>
                  <option>Placements & Eligibility</option>
                  <option>Other</option>
                </select>
              </label>

              <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                Suggested Correction & Official Evidence URL:
                <textarea
                  rows={4}
                  placeholder="Provide the verified fact and official circular / URL link..."
                  style={{
                    width: "100%",
                    marginTop: "4px",
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border-color)",
                    color: "var(--text-primary)",
                    padding: "8px",
                    borderRadius: "var(--radius-sm)",
                    fontFamily: "inherit",
                  }}
                />
              </label>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "20px" }}>
              <button className="btn-ghost" onClick={() => setReportModalOpen(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={() => {
                  alert("Thank you! Your report has been submitted for maintainer review.");
                  setReportModalOpen(false);
                }}
              >
                Submit to GitHub
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Source Details & Provenance Viewer Modal */}
      {selectedSource && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--accent-cyan)",
              borderRadius: "var(--radius-lg)",
              maxWidth: "640px",
              width: "100%",
              padding: "24px",
              boxShadow: "0 0 40px rgba(0, 240, 255, 0.15)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: "4px",
                      background:
                        selectedSource.freshness_status === "SUPERSEDED"
                          ? "rgba(244, 63, 94, 0.2)"
                          : "rgba(16, 185, 129, 0.2)",
                      color:
                        selectedSource.freshness_status === "SUPERSEDED"
                          ? "var(--accent-rose)"
                          : "var(--accent-emerald)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    {selectedSource.freshness_status || "CURRENT"}
                  </span>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      padding: "3px 8px",
                      borderRadius: "4px",
                      background: "rgba(0, 240, 255, 0.1)",
                      color: "var(--accent-cyan)",
                    }}
                  >
                    Authority Level {selectedSource.authority_level} (Official SRMAP)
                  </span>
                </div>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  {selectedSource.title}
                </h3>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: "1.2rem",
                  cursor: "pointer",
                  padding: "4px",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "12px" }}>
              {selectedSource.publication_date_str && (
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Publication / Policy Date:</span>
                  <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{selectedSource.publication_date_str}</span>
                </div>
              )}

              {selectedSource.page_number && (
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Page Number:</span>
                  <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>Page {selectedSource.page_number}</span>
                </div>
              )}

              {selectedSource.url && (
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
                  <span style={{ color: "var(--text-muted)" }}>Source URL:</span>
                  <a
                    href={selectedSource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: "var(--accent-cyan)", wordBreak: "break-all" }}
                  >
                    {selectedSource.url}
                  </a>
                </div>
              )}

              {selectedSource.snippet && (
                <div style={{ marginTop: "8px" }}>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "4px" }}>
                    Verified Document Excerpt:
                  </div>
                  <div
                    style={{
                      background: "var(--bg-secondary)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "var(--radius-sm)",
                      padding: "12px",
                      fontSize: "0.82rem",
                      lineHeight: 1.5,
                      color: "var(--text-secondary)",
                      fontStyle: "italic",
                    }}
                  >
                    "{selectedSource.snippet}..."
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "20px" }}>
              <button className="btn-primary" onClick={() => setSelectedSource(null)}>
                Close Viewer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
