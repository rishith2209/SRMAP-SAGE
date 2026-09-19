import json
from services.ingestion.web_crawler import WebCrawler, OFFICIAL_WEB_REGISTRY
from services.ingestion.chunker import split_into_chunks

crawler = WebCrawler()
wiki_cfg = next(c for c in OFFICIAL_WEB_REGISTRY if "wikipedia" in c["url"])
res = crawler.fetch_source(wiki_cfg)
print(f"Wikipedia Status: {res['status']} | Title: {res['title']} | Text length: {len(res['text'])}")

if res["status"] == "SUCCESS":
    with open("data/knowledge_catalog.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    src_id = "web_wikipedia_srmap"
    data["sources"][src_id] = {
        "id": src_id,
        "title": res["title"],
        "url": res["url"],
        "source_type": res["source_type"],
        "authority_level": 5,
        "content_hash": res["content_hash"],
        "status": "INGESTED"
    }
    chunks = split_into_chunks(res["text"], 1, res["title"], "web_scrape")
    for ch in chunks:
        ch["source_id"] = src_id
        ch["source_title"] = res["title"]
        ch["authority_level"] = 5
        ch["domain"] = "GENERAL_UNIVERSITY_INFORMATION"
    data["chunks"].extend(chunks)
    data["sources_count"] = len(data["sources"])
    data["chunks_count"] = len(data["chunks"])
    with open("data/knowledge_catalog.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Added {len(chunks)} Wikipedia chunks. Total chunks in catalog: {data['chunks_count']}")
