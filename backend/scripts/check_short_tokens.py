import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.global_disease_matrix_service import global_disease_matrix_service

global_disease_matrix_service.ensure_loaded()
print(f"Total diseases: {global_disease_matrix_service.disease_count}")
print(f"Total manifestations: {len(global_disease_matrix_service._inverted_index)}")

# Check 'h' in inverted index
if "h" in global_disease_matrix_service._inverted_index:
    print("Found 'h' in inverted index! Posting list:", global_disease_matrix_service._inverted_index["h"])
    print("IDF weight for 'h':", global_disease_matrix_service._idf_weights.get("h"))
else:
    print("'h' not found in inverted index.")

# Check short tokens in inverted index
short_tokens = [k for k in global_disease_matrix_service._inverted_index if len(k) < 3]
print(f"Total short tokens (<3 chars) in inverted index: {len(short_tokens)}")
print("Sample short tokens:", short_tokens[:20])
