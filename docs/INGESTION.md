# Ingestion Pipeline Guide

## Overview
The ingestion pipeline processes documents (PDF, HTML, DOCX) and structured records into PostgreSQL with vector embeddings and full-text search indexes.

## Pipeline Lifecycle
```
File/URL Input 
  ──> Hash Check (SHA-256)
  ──> Domain Whitelist Validation
  ──> Content Extraction (PyMuPDF / Trafilatura)
  ──> Metadata Extraction (Author, Date, Category, Authority Tier)
  ──> Semantic Section Chunking
  ──> Embedding Computation (Gemini / Nomic)
  ──> Atomic DB Upsert
```

## Running Ingestion
Once PDF documents are placed in `data/docs/`:
```bash
python -m src.services.ingestion_service --input data/docs/
```

Or for structured JSON seeds:
```bash
python -m src.services.seed_loader --seeds-dir data/seeds/
```
