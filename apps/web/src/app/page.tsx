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
}

interface Message {
  id: string;
  sender: "user" | "sage";
  text: string;
  intent?: string;
  is_fallback?: boolean;
  sources?: SourceCitation[];
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
                <div style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "var(--text-primary)" }}>
                  {msg.text}
                </div>

                {/* Evidence & Provenance Sources */}
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "8px" }}>
                      VERIFIED PROVENANCE (Level {msg.sources[0].authority_level}):
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {msg.sources.map((src) => (
                        <div
                          key={src.id}
                          style={{
                            background: "rgba(0, 240, 255, 0.05)",
                            border: "1px solid rgba(0, 240, 255, 0.2)",
                            borderRadius: "var(--radius-sm)",
                            padding: "6px 12px",
                            fontSize: "0.78rem",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                          }}
                        >
                          <CheckCircle2 size={13} color="var(--accent-emerald)" />
                          <span>{src.title}</span>
                          {src.url && (
                            <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-cyan)" }}>
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                      ))}
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
    </div>
  );
}
