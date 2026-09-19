# SRMAP SAGE — Student Assistance & Guidance Engine

<div align="center">

**An open-source, evidence-grounded digital guidance engine for SRM University-AP students.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-blue.svg)](https://github.com/pgvector/pgvector)

</div>

---

## 🌟 The Core Vision

**SRMAP SAGE** is an open-source, multi-source digital knowledge and assistance engine built specifically for **SRM University-AP (SRMAP)**.

Unlike generic chatbots that hallucinate policies and guess office locations, SAGE operates under a strict principle:

> **`EVIDENCE → REASONING → ANSWER`**
>
> If verified evidence is absent or ambiguous, SAGE explicitly responds:  
> *"I couldn't find a reliable official SRMAP source confirming this information."*

---

## 🏛️ System Architecture

SAGE rejects the single-vector-database anti-pattern. Instead, it utilizes a poly-engine architecture tailored to the nature of student inquiries:

```
                               ┌───────────────────────────┐
                               │       User Request        │
                               └─────────────┬─────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │  Question & Intent Router │
                               └─────────────┬─────────────┘
                  ┌──────────────────────────┼──────────────────────────┐
                  ▼                          ▼                          ▼
      ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
      │ Document RAG Engine   │  │ Structured DB Engine  │  │ Campus Spatial Engine │
      │ (PDFs, Circulars,     │  │ (Faculty, Cabins,     │  │ (Topological Routes,  │
      │  Regulations, Policies│  │  Departments, Stats)  │  │  Blocks, Floors)      │
      └───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
                  │                          │                          │
                  └──────────────────────────┼──────────────────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │ Aggregator & Conflict Chk │
                               └─────────────┬─────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │  Model Provider (Gemini / │
                               │  Ollama / Local)          │
                               └─────────────┬─────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │    Adaptive UI Payload    │
                               │ (Procedure / Card / Route)│
                               └───────────────────────────┘
```

1. **Document Knowledge**: Policies, academic regulations, handbooks, circulars, and forms via hybrid vector (pgvector) + BM25 search.
2. **Structured Knowledge**: Faculty roster, cabin numbers, department mapping, and placement statistics via relational PostgreSQL tables.
3. **Spatial & Campus Knowledge**: Building blocks, rooms, and walking pathfinding via topological node-edge graph.
4. **Live Web Knowledge**: Controlled allowlist scraper targeting official university notice boards and announcements.
5. **Community Verification Loop**: Direct integration with GitHub Issues enabling students to report discrepancies for maintainer review.

---

## 📂 Repository Structure

```
SRMAP-SAGE/
├── .github/                    # Issue & PR templates for community corrections
├── apps/
│   ├── api/                    # FastAPI backend & orchestration service
│   │   ├── src/
│   │   │   ├── api/            # API v1 route handlers
│   │   │   ├── core/           # Config, database, security
│   │   │   ├── engines/        # RAG, SQL, Spatial, Web, Conflict, Router
│   │   │   ├── models/         # SQLAlchemy DB models & Pydantic schemas
│   │   │   ├── providers/      # LLM provider abstraction (Gemini, Ollama, Mock)
│   │   │   └── services/       # Ingestion & GitHub sync services
│   │   ├── tests/
│   │   └── requirements.txt
│   └── web/                    # Next.js 15 App Router frontend
├── services/
│   └── crawler/                # Scheduled background scraper & PDF extractor
├── data/
│   ├── seeds/                  # Structured seed files (faculty, campus, domains)
│   ├── docs/                   # Reference official documents & circulars
│   └── benchmark/              # Evaluation QA test suite
├── docker/
│   ├── docker-compose.yml      # Local dev services (Postgres + pgvector)
│   └── init-db.sql             # DB initialization & extension setup
├── docs/                       # Architecture, Ingestion & Contributing guides
├── .env.example
├── LICENSE
└── README.md
```

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose**

### 2. Setup Environment
```bash
cp .env.example .env
```
Fill in your `GEMINI_API_KEY` (or configure local Ollama).

### 3. Start Database (PostgreSQL + pgvector)
```bash
docker compose -f docker/docker-compose.yml up -d db
```

### 4. Setup & Run Backend API
```bash
cd apps/api
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### 5. Ingestion, Evaluation & Freshness Verification
```bash
# Run the complete Phase 3 evaluation suite (Temporal, Source Priority, Negative, Security)
python services/ingestion/eval_phase3.py

# Run unit tests across the entire repository
python -m pytest

# Run live circular and notice discovery from srmap.edu.in
python -c "import asyncio; from services.ingestion.circular_discovery import CircularDiscoveryEngine; asyncio.run(CircularDiscoveryEngine().discover_and_catalog())"
```

### Verified Phase 3 Benchmark Metrics
- **Recall@1:** 100.00% (28/28)
- **Recall@3:** 100.00% (28/28)
- **Recall@5:** 100.00% (28/28)
- **MRR:** 1.0000
- **Grounded Answer Rate:** 100.00%
- **Unsupported / Hallucination Rate:** 0.00%
- **Correct Refusal Rate:** 100.00%
- **Temporal Routing Accuracy:** 100.00% (7/7)
- **Source Hierarchy Accuracy:** 100.00% (4/4)
- **Prompt Injection Defense:** 100.00% (2/2)

### 6. Setup & Run Frontend UI
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser to view the interactive interface with live provenance cards and freshness status badges.

---

## 🤝 Community & Contributions

Found outdated or incorrect information? SAGE is community-maintained.  
Please submit an issue using our [Content Correction Template](.github/ISSUE_TEMPLATE/content_correction.md) or open a Pull Request.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
