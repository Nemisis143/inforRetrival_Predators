import os
import sys
import json
import time
from rocchio import RocchioExpander
from expansion_clusters import ClusterExpander

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer

def run_final_tests():
    print("--- STEP 1: Loading & Optimizing Data ---", flush=True)
    start_load = time.time()
    
    indexer = PredatorIndexer("data/pages")
    indexer.load_from_disk()
    indexer.load_mapping("data/url_mapping.jsonl")
    indexer.load_link_scores("link_analysis_scores.pkl")
    
    # This will trigger the Forward Index building
    clusters = ClusterExpander(indexer)
    rocchio = RocchioExpander(indexer)
    
    print(f"Total Initialization Time: {time.time()-start_load:.1f}s", flush=True)
    
    # Load all queries
    rocchio_queries = []
    cluster_queries = []
    
    current_section = None
    with open("query_expansion/test_queries.txt", "r") as f:
        for line in f:
            line = line.strip()
            if "Rocchio" in line: current_section = "rocchio"
            elif "Cluster" in line: current_section = "cluster"
            elif line and line[0].isdigit():
                query = line.split(". ", 1)[1]
                if current_section == "rocchio": rocchio_queries.append(query)
                else: cluster_queries.append(query)

    # 1. Run Rocchio Tests (20)
    print(f"\n--- STEP 2: Running {len(rocchio_queries)} Rocchio Queries (Optimized) ---", flush=True)
    rocchio_results = {}
    for i, q in enumerate(rocchio_queries, 1):
        start_q = time.time()
        initial_results = indexer.fused_search(q, top_n=3)
        rel_docs = []
        for res in initial_results:
            for doc_id, url in indexer.url_map.items():
                if url == res['url']:
                    rel_docs.append(doc_id)
                    break
        
        expanded = rocchio.expand(q, rel_docs, [])
        rocchio_results[q] = {"expanded_terms": [t[0] for t in expanded]}
        print(f"[{i}/20] '{q}' -> Done ({time.time()-start_q:.2f}s)", flush=True)

    # 2. Run Cluster Tests (50)
    print(f"\n--- STEP 3: Running {len(cluster_queries)} Cluster Queries (Optimized) ---", flush=True)
    cluster_results = {}
    for i, q in enumerate(cluster_queries, 1):
        start_q = time.time()
        word = q.split()[0].lower()
        
        assoc = clusters.get_association_expansion(word, top_k=3)
        metric = clusters.get_metric_expansion(word, top_k=3)
        scalar = clusters.get_scalar_expansion(word, top_k=3)
        
        cluster_results[q] = {
            "association": [t[0] for t in assoc],
            "metric": [t[0] for t in metric],
            "scalar": [t[0] for t in scalar]
        }
        print(f"[{i}/50] '{q}' -> Done ({time.time()-start_q:.2f}s)", flush=True)

    # Save final results
    with open("query_expansion/query_expansion_results.json", "w") as f:
        json.dump(rocchio_results, f, indent=4)
    with open("query_expansion/cluster_expansion_results.json", "w") as f:
        json.dump(cluster_results, f, indent=4)
        
    print("\nALL TESTS COMPLETED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    run_final_tests()
