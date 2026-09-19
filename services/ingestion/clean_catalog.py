import json

with open("data/knowledge_catalog.json", "r", encoding="utf-8") as f:
    data = json.load(f)

original_count = len(data["chunks"])
# Keep only chunks with at least 25 characters of meaningful policy text
clean_chunks = [ch for ch in data["chunks"] if len(ch.get("content", "").strip()) >= 25]

print(f"Original chunks: {original_count} -> Clean substantive chunks: {len(clean_chunks)}")
data["chunks"] = clean_chunks
data["chunks_count"] = len(clean_chunks)

with open("data/knowledge_catalog.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
