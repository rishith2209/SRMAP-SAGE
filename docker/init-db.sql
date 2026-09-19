-- ==============================================================================
-- SRMAP SAGE — Database Initialization Script
-- Initializes PostgreSQL extensions, tables, and indices for pgvector & full-text
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. SOURCES & PROVENANCE REGISTRY
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    url TEXT UNIQUE,
    source_type VARCHAR(50) NOT NULL, -- 'pdf', 'webpage', 'notice', 'structured_dataset'
    authority_level INT NOT NULL CHECK (authority_level BETWEEN 1 AND 4),
    published_at TIMESTAMPTZ,
    crawled_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url);
CREATE INDEX IF NOT EXISTS idx_sources_authority ON sources(authority_level);

-- 2. DOCUMENT CHUNKS (HYBRID VECTOR + FULL-TEXT SEARCH)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    section_heading TEXT,
    page_number INT,
    content TEXT NOT NULL,
    token_count INT NOT NULL,
    tsv_content TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    embedding vector(768) -- Default for text-embedding-004 / nomic-embed
);

CREATE INDEX IF NOT EXISTS idx_chunks_source ON document_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON document_chunks USING GIN(tsv_content);
-- HNSW index for vector cosine similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 3. STRUCTURED DEPARTMENTS & FACULTY
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    block_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS faculty (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    designation VARCHAR(100) NOT NULL,
    department_id VARCHAR(50) REFERENCES departments(id) ON DELETE SET NULL,
    cabin_number VARCHAR(100),
    block VARCHAR(50),
    floor VARCHAR(20),
    email VARCHAR(200),
    phone VARCHAR(50),
    research_areas TEXT[],
    profile_url TEXT,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_faculty_name_trgm ON faculty USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department_id);

-- 4. STRUCTURED PLACEMENT RECORDS
CREATE TABLE IF NOT EXISTS placement_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    academic_year VARCHAR(20) NOT NULL, -- e.g. '2023-2024'
    company_name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    ctc_lpa NUMERIC(6, 2),
    offers_count INT DEFAULT 1,
    eligible_departments TEXT[],
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_placement_company_trgm ON placement_stats USING GIN (company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_placement_year ON placement_stats(academic_year);

-- 5. CAMPUS SPATIAL TOPOLOGY (NODES & EDGES)
CREATE TABLE IF NOT EXISTS campus_nodes (
    id VARCHAR(100) PRIMARY KEY, -- e.g. 'block_3_ground_entrance'
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'building', 'hostel', 'lab', 'office', 'dining', 'medical'
    block_code VARCHAR(20),
    floor VARCHAR(20),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    landmarks TEXT[]
);

CREATE TABLE IF NOT EXISTS campus_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_node VARCHAR(100) NOT NULL REFERENCES campus_nodes(id) ON DELETE CASCADE,
    to_node VARCHAR(100) NOT NULL REFERENCES campus_nodes(id) ON DELETE CASCADE,
    distance_meters NUMERIC(6, 2) NOT NULL,
    accessibility_type VARCHAR(50) DEFAULT 'walking', -- 'walking', 'stairs', 'elevator', 'wheelchair'
    instructions TEXT
);

-- 6. COMMUNITY FEEDBACK & DISCREPANCY REPORTS
CREATE TABLE IF NOT EXISTS community_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    generated_answer TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    report_reason VARCHAR(100) NOT NULL,
    suggested_correction TEXT,
    provided_evidence_url TEXT,
    github_issue_number INT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'verified', 'rejected', 'merged'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
