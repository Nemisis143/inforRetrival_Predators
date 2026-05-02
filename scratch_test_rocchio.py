import os
import sys
import time

from indexing_relevance.indexer import PredatorIndexer
from query_expansion.rocchio import RocchioExpander

print("Loading indexer...")
indexer = PredatorIndexer("data/pages")
indexer.load_from_disk()
indexer.load_mapping("data/url_mapping.jsonl")
indexer.load_link_scores("link_analysis_scores.pkl")

rocchio = RocchioExpander(indexer)
q = "African Lion hunting habits"
print(f"Running Rocchio for: {q}")
initial_results = indexer.fused_search(q, top_n=50)
rel_docs = []
non_rel_docs = []
for i, res in enumerate(initial_results):
    for doc_id, url in indexer.url_map.items():
        if url == res['url']:
            if i < 3:
                rel_docs.append(doc_id)
            elif i >= 40:
                non_rel_docs.append(doc_id)
            break

expanded = rocchio.expand(q, rel_docs, non_rel_docs)
print("Expanded terms:")
for term, score in expanded:
    print(f"  - {term}: {score:.4f}")
