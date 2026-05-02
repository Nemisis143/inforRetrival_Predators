import os
import sys
import json
import re
import pickle
from collections import defaultdict

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer
from query_expansion.rocchio import RocchioExpander
from query_expansion.expansion_clusters import ClusterExpander

def get_doc_metadata(doc_id, pages_dir):
    path = os.path.join(pages_dir, doc_id)
    title = "Untitled Page"
    snippet = "No snippet available."
    
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                if lines:
                    title = lines[0][:100] # Use first line as title
                    # Create a snippet from the first few sentences/lines
                    full_text = " ".join(lines)
                    snippet = full_text[:200] + "..."
        except:
            pass
    return title, snippet

def generate_demo_json():
    print("Initializing Demo Data Generator...")
    indexer = PredatorIndexer("data/pages")
    indexer.load_from_disk()
    indexer.load_mapping("data/url_mapping.jsonl")
    indexer.load_link_scores("link_analysis_scores.pkl")
    
    rocchio = RocchioExpander(indexer)
    clusters = ClusterExpander(indexer)
    
    # Check for command line argument
    if len(sys.argv) > 1:
        demo_queries = [" ".join(sys.argv[1:])]
    else:
        demo_queries = [
            "African Lion hunting",
            "Great White Shark migration",
            "Apex predators"
        ]
    
    demo_data = {}
    
    for query in demo_queries:
        print(f"Processing query: {query}")
        q_data = {
            "original_query": query,
            "results": {}
        }
        
        # 1. Base (TF-IDF only, No PageRank)
        # We need a way to disable PageRank. Let's mock it or temporarily swap it.
        original_pr = indexer.pagerank
        indexer.pagerank = {} # Disable PR
        base_results = indexer.fused_search(query, top_n=5)
        indexer.pagerank = original_pr # Restore PR
        
        q_data["results"]["base_tfidf"] = []
        for res in base_results:
            doc_id = None
            for d_id, url in indexer.url_map.items():
                if url == res['url']:
                    doc_id = d_id
                    break
            title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
            q_data["results"]["base_tfidf"].append({
                "url": res['url'],
                "title": title,
                "snippet": snippet,
                "score": res['score']
            })
            
        # 2. Base + Link Analysis (PageRank)
        pr_results = indexer.fused_search(query, top_n=5)
        q_data["results"]["with_pagerank"] = []
        for res in pr_results:
            doc_id = None
            for d_id, url in indexer.url_map.items():
                if url == res['url']:
                    doc_id = d_id
                    break
            title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
            q_data["results"]["with_pagerank"].append({
                "url": res['url'],
                "title": title,
                "snippet": snippet,
                "score": res['score']
            })
            
        # 3. Expanded (Rocchio)
        # Get expanded query first
        # Rocchio needs rel_docs. Let's use top 3 from base search as pseudo-feedback
        rel_docs = []
        for res in base_results[:3]:
            for d_id, url in indexer.url_map.items():
                if url == res['url']:
                    rel_docs.append(d_id)
                    break
        
        expanded_rocchio = rocchio.expand(query, rel_docs, [])
        expanded_q_rocchio = query + " " + " ".join([t[0] for t in expanded_rocchio])
        q_data["expanded_query_rocchio"] = expanded_q_rocchio
        
        rocchio_results = indexer.fused_search(expanded_q_rocchio, top_n=5)
        q_data["results"]["with_rocchio"] = []
        for res in rocchio_results:
            doc_id = None
            for d_id, url in indexer.url_map.items():
                if url == res['url']:
                    doc_id = d_id
                    break
            title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
            q_data["results"]["with_rocchio"].append({
                "url": res['url'],
                "title": title,
                "snippet": snippet,
                "score": res['score']
            })
            
        # 4. Expanded (Cluster)
        # Just pick the first word for cluster expansion for simplicity in demo
        word = query.split()[0].lower()
        cluster_terms = clusters.get_association_expansion(word, top_k=3)
        expanded_q_cluster = query + " " + " ".join([t[0] for t in cluster_terms])
        q_data["expanded_query_cluster"] = expanded_q_cluster
        
        cluster_results = indexer.fused_search(expanded_q_cluster, top_n=5)
        q_data["results"]["with_clustering"] = []
        for res in cluster_results:
            doc_id = None
            for d_id, url in indexer.url_map.items():
                if url == res['url']:
                    doc_id = d_id
                    break
            title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
            q_data["results"]["with_clustering"].append({
                "url": res['url'],
                "title": title,
                "snippet": snippet,
                "score": res['score']
            })
            
        demo_data[query] = q_data
        
    with open("demo_results_for_frontend.json", "w") as f:
        json.dump(demo_data, f, indent=4)
    print("Demo data generated successfully in 'demo_results_for_frontend.json'")

if __name__ == "__main__":
    generate_demo_json()
