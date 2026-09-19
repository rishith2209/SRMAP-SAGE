import argparse
import sys
from services.ingestion.run_pipeline import run_ingestion
from services.ingestion.regression_eval import evaluate_retrieval


def main():
    parser = argparse.ArgumentParser(description="SRMAP SAGE Ingestion & Evaluation CLI")
    parser.add_argument(
        "--mode",
        choices=["all", "docs", "web", "eval"],
        default="all",
        help="Execution mode: 'all' (web+docs), 'docs' (PDFs/OCR), 'web' (crawling), 'eval' (regression tests)"
    )

    args = parser.parse_args()

    if args.mode in ["all", "docs", "web"]:
        print(f"=== Starting SAGE Ingestion Pipeline [Mode: {args.mode}] ===")
        report, _ = run_ingestion()
        print("\n=== Ingestion Completed ===")
        print(f"Documents Discovered: {report['documents_discovered']}")
        print(f"Documents Ingested:   {report['documents_ingested']}")
        print(f"Pages Scanned/OCR'd:  {report['documents_ocr_success']}")
        print(f"Total Chunks Created: {report['chunks_created']}")
        print(f"Web Sources Crawled:  {len(report['web_sources_crawled'])}")
        print(f"Auth Required Sites:  {len(report['auth_required_sources'])}")

    if args.mode in ["all", "eval"]:
        print("\n=== Running Grounded Regression Evaluation ===")
        eval_results = evaluate_retrieval()
        passed = sum(1 for r in eval_results if r["status"] == "PASSED")
        print(f"Evaluated {len(eval_results)} Questions: {passed}/{len(eval_results)} Passed with Verified Provenance.")


if __name__ == "__main__":
    main()
