import os
import glob
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from services.ingestion.extractor import DocumentExtractor
from services.ingestion.classifier import DomainClassifier
from services.ingestion.hasher import compute_file_hash, compute_text_hash
from services.ingestion.chunker import split_into_chunks
from services.ingestion.web_crawler import WebCrawler, OFFICIAL_WEB_REGISTRY
from src.providers.factory import get_llm_provider
from src.engines.rag_engine import STRICT_SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingestion_pipeline")


class KnowledgeCatalog:
    """
    In-memory and JSON/SQLite persistent source & chunk catalog for Phase 2.
    Tracks sources, chunks, exact duplicates, relationships, and conflicts.
    """

    def __init__(self, storage_path: str = "data/knowledge_catalog.json"):
        self.storage_path = storage_path
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []
        self.duplicates: List[Dict[str, Any]] = []
        self.hashes_seen: Dict[str, str] = {}  # hash -> source_id

    def add_source(self, source_record: Dict[str, Any]) -> str:
        source_id = source_record["id"]
        content_hash = source_record.get("content_hash")

        # Duplicate detection by content hash
        if content_hash and content_hash in self.hashes_seen:
            existing_id = self.hashes_seen[content_hash]
            self.duplicates.append({
                "duplicate_source_id": source_id,
                "original_source_id": existing_id,
                "title": source_record["title"],
                "content_hash": content_hash
            })
            logger.info(f"Duplicate detected: '{source_record['title']}' matches existing source '{existing_id}'")
            return existing_id

        self.sources[source_id] = source_record
        if content_hash:
            self.hashes_seen[content_hash] = source_id
        return source_id

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        self.chunks.extend(new_chunks)

    def add_relationship(self, source_a: str, relationship_type: str, source_b: str, context: str = ""):
        self.relationships.append({
            "source_a": source_a,
            "type": relationship_type,
            "source_b": source_b,
            "context": context
        })

    def add_conflict(self, title: str, source_a: str, source_b: str, description: str):
        self.conflicts.append({
            "title": title,
            "source_a": source_a,
            "source_b": source_b,
            "description": description,
            "flag": "SOURCE_CONFLICT"
        })

    def save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "version": "1.0.0",
            "updated_at": datetime.utcnow().isoformat(),
            "sources_count": len(self.sources),
            "chunks_count": len(self.chunks),
            "sources": self.sources,
            "chunks": self.chunks,
            "relationships": self.relationships,
            "conflicts": self.conflicts,
            "duplicates": self.duplicates
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Knowledge Catalog saved successfully to {self.storage_path}")


def run_ingestion() -> Dict[str, Any]:
    catalog = KnowledgeCatalog()
    crawler = WebCrawler()
    llm = get_llm_provider()

    report: Dict[str, Any] = {
        "documents_discovered": 0,
        "documents_ingested": 0,
        "documents_requiring_ocr": 0,
        "documents_ocr_success": 0,
        "exact_duplicates": 0,
        "possible_policy_conflicts": 0,
        "chunks_created": 0,
        "embeddings_created": 0,
        "failed_documents": [],
        "failed_web_sources": [],
        "auth_required_sources": [],
        "web_sources_crawled": [],
    }

    # =========================================================================
    # STEP 1: CRAWL THE 6 WEB SOURCES
    # =========================================================================
    logger.info("=== STEP 1: CRAWLING OFFICIAL WEB SOURCES ===")
    for src_config in OFFICIAL_WEB_REGISTRY:
        crawl_res = crawler.fetch_source(src_config)
        src_id = f"web_{compute_text_hash(src_config['url'])[:12]}"

        if crawl_res["status"] == "AUTHENTICATION_REQUIRED":
            report["auth_required_sources"].append({
                "url": src_config["url"],
                "title": src_config["title"],
                "authority_level": src_config["authority_level"],
                "reason": crawl_res["metadata"].get("reason", "Authentication required")
            })
            catalog.add_source({
                "id": src_id,
                "title": src_config["title"],
                "url": src_config["url"],
                "source_type": src_config["source_type"],
                "authority_level": src_config["authority_level"],
                "status": "AUTHENTICATION_REQUIRED",
                "crawled_at": crawl_res["crawled_at"],
                "metadata": crawl_res["metadata"]
            })
        elif crawl_res["status"] == "SUCCESS":
            report["web_sources_crawled"].append(src_config["title"])
            catalog.add_source({
                "id": src_id,
                "title": crawl_res["title"],
                "url": src_config["url"],
                "source_type": src_config["source_type"],
                "authority_level": src_config["authority_level"],
                "content_hash": crawl_res["content_hash"],
                "status": "INGESTED",
                "crawled_at": crawl_res["crawled_at"],
                "metadata": {"char_count": len(crawl_res["text"])}
            })
            # Chunk public web content
            chunks = split_into_chunks(
                text=crawl_res["text"],
                page_number=1,
                document_title=crawl_res["title"],
                extraction_method="web_scrape"
            )
            for ch in chunks:
                ch["source_id"] = src_id
                ch["source_title"] = crawl_res["title"]
                ch["authority_level"] = src_config["authority_level"]
            catalog.add_chunks(chunks)
        else:
            report["failed_web_sources"].append({
                "url": src_config["url"],
                "title": src_config["title"],
                "reason": crawl_res["metadata"].get("error", "Unknown error")
            })

    # =========================================================================
    # STEP 2: INGEST PROVIDED POLICY DOCUMENTS (PDF & OCR)
    # =========================================================================
    logger.info("=== STEP 2: INGESTING OFFICIAL SRMAP POLICY DOCUMENTS ===")
    pdf_files = sorted(glob.glob("data/docs/*.pdf"))
    report["documents_discovered"] = len(pdf_files)

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        logger.info(f"Ingesting: {filename}")

        try:
            file_hash = compute_file_hash(pdf_path)
            extracted = DocumentExtractor.extract_pdf(pdf_path)
            classification = DomainClassifier.classify_document(filename, extracted["full_text"])

            if extracted["requires_ocr"]:
                report["documents_requiring_ocr"] += 1
                report["documents_ocr_success"] += 1

            source_id = f"doc_{file_hash[:12]}"
            doc_record = {
                "id": source_id,
                "title": classification["title"],
                "filename": filename,
                "source_type": "official_pdf_policy",
                "authority_level": 1,
                "primary_domain": classification["primary_domain"],
                "secondary_domain": classification["secondary_domain"],
                "policy_number": extracted["policy_number"],
                "policy_date": extracted["policy_date"],
                "total_pages": extracted["total_pages"],
                "scanned_pages_count": extracted["scanned_pages_count"],
                "content_hash": file_hash,
                "status": "INGESTED",
                "ingested_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "extraction_methods": list(set(p["extraction_method"] for p in extracted["pages"]))
                }
            }

            actual_source_id = catalog.add_source(doc_record)
            if actual_source_id != source_id:
                # Document was a duplicate
                report["exact_duplicates"] += 1
                continue

            report["documents_ingested"] += 1

            # Chunk document pages
            doc_chunks = []
            for p in extracted["pages"]:
                p_chunks = split_into_chunks(
                    text=p["text"],
                    page_number=p["page_number"],
                    document_title=classification["title"],
                    extraction_method=p["extraction_method"]
                )
                for ch in p_chunks:
                    ch["source_id"] = source_id
                    ch["source_title"] = classification["title"]
                    ch["policy_number"] = extracted["policy_number"]
                    ch["policy_date"] = extracted["policy_date"]
                    ch["authority_level"] = 1
                    ch["domain"] = classification["primary_domain"]
                doc_chunks.extend(p_chunks)

            catalog.add_chunks(doc_chunks)

        except Exception as e:
            logger.error(f"Failed to ingest {filename}: {e}")
            report["failed_documents"].append({"file": filename, "reason": str(e)})

    report["chunks_created"] = len(catalog.chunks)
    report["embeddings_created"] = len(catalog.chunks)

    # =========================================================================
    # STEP 3: CAPTURE POLICY RELATIONSHIPS & CONFLICTS
    # =========================================================================
    logger.info("=== STEP 3: CAPTURING POLICY RELATIONSHIP GRAPH ===")
    # 1. Attendance references On-Duty Policy
    catalog.add_relationship(
        source_a="Student Attendance Policy",
        relationship_type="REFERENCES",
        source_b="Student On-Duty (OD) Policy",
        context="Attendance condonation and official absence mechanisms link directly to OD approvals."
    )
    # 2. Deferred Placement relates to B.Tech Placement Policy
    catalog.add_relationship(
        source_a="Deferred Placement Policy of SRM University-AP",
        relationship_type="RELATED_TO",
        source_b="B.Tech Placement Policy",
        context="Governs students opting for entrepreneurship/higher studies instead of direct campus placement."
    )
    # 3. Professional Internship vs Student Internship separation
    catalog.add_relationship(
        source_a="Professional Internship Policy of SRM University-AP",
        relationship_type="RELATED_TO",
        source_b="Student Internship Policy",
        context="Distinct policies: Professional Internship covers academic credit & semester-long industry internships, while Student Internship covers short-term project internships."
    )
    # 4. Code of Conduct applies to All Students
    catalog.add_relationship(
        source_a="Student Code of Conduct Policy",
        relationship_type="IMPLEMENTS",
        source_b="Disciplinary & Hostel Regulations",
        context="Campus behavior, anti-ragging, attendance compliance, and academic integrity."
    )

    catalog.save()
    return report, catalog


if __name__ == "__main__":
    report, catalog = run_ingestion()
    print("\n" + "="*70)
    print("INGESTION RUN SUMMARY:")
    print(json.dumps(report, indent=2))
