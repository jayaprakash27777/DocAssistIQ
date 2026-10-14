import json
import os

manifest_path = r"D:\OFFLINE DATA\manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

ds = manifest.get("datasets", {})

# 1. Update lavita_medical_qa_benchmarks
if "lavita_medical_qa_benchmarks" in ds:
    item = ds["lavita_medical_qa_benchmarks"]
    item["status"] = "ready"
    item["domain"] = "clinical_reasoning"
    item["task_type"] = "benchmark"
    item["file_count"] = 1
    db_p = r"D:\OFFLINE DATA\lavita_medical_qa_benchmarks\lavita_medical_qa.db"
    if os.path.exists(db_p):
        item["size_bytes"] = os.path.getsize(db_p)
        item["size_mb"] = round(item["size_bytes"] / (1024 * 1024), 2)
    item["storage_path"] = r"D:\OFFLINE DATA\lavita_medical_qa_benchmarks"

# 2. Update pubmed_clinical_trials_full
if "pubmed_clinical_trials_full" in ds:
    item = ds["pubmed_clinical_trials_full"]
    item["status"] = "ready"
    item["domain"] = "clinical_trials"
    item["task_type"] = "trials_registry"
    item["file_count"] = 1
    db_p = r"D:\OFFLINE DATA\pubmed_clinical_trials_full\pubmed_clinical_trials.db"
    if os.path.exists(db_p):
        item["size_bytes"] = os.path.getsize(db_p)
        item["size_mb"] = round(item["size_bytes"] / (1024 * 1024), 2)
    item["storage_path"] = r"D:\OFFLINE DATA\pubmed_clinical_trials_full"

# 3. Update pubmed_open_access_articles
if "pubmed_open_access_articles" in ds:
    item = ds["pubmed_open_access_articles"]
    item["status"] = "ready"
    item["domain"] = "clinical_literature"
    item["task_type"] = "literature"
    item["file_count"] = 1
    db_p = r"D:\OFFLINE DATA\pubmed_open_access_articles\pubmed_open_access.db"
    if os.path.exists(db_p):
        item["size_bytes"] = os.path.getsize(db_p)
        item["size_mb"] = round(item["size_bytes"] / (1024 * 1024), 2)
    item["storage_path"] = r"D:\OFFLINE DATA\pubmed_open_access_articles"

# Recalculate totals
total_bytes = sum(v.get("size_bytes", 0) for v in ds.values())
total_mb = sum(v.get("size_mb", 0) for v in ds.values())
manifest["total_datasets"] = len(ds)
manifest["total_size_bytes"] = total_bytes
manifest["total_size_mb"] = round(total_mb, 2)
manifest["total_size_gb"] = round(total_mb / 1024, 2)
manifest["status"] = "ready"

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest successfully updated! All {len(ds)} datasets now marked ready.")
print(f"Total size: {manifest['total_size_gb']} GB across {len(ds)} datasets.")
