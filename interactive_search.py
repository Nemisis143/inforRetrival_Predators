import os
import sys
import json

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
                    title = lines[0][:100]
                    full_text = " ".join(lines)
                    snippet = full_text[:200] + "..."
        except:
            pass
    return title, snippet

def run_interactive():
    print("\n--- Predator Search Engine: Ad-hoc Query Tool ---")
    print("Loading index and scores (takes ~35s)...")
    
    indexer = PredatorIndexer("data/pages")
    indexer.load_from_disk()
    indexer.load_mapping("data/url_mapping.jsonl")
    indexer.load_link_scores("link_analysis_scores.pkl")
    
    rocchio = RocchioExpander(indexer)
    clusters = ClusterExpander(indexer)
    
    print("\n--- SYSTEM READY ---")
    print("Type your query and press Enter. Type 'exit' to quit.")

    while True:
        try:
            query = input("\nSearch Query > ").strip()
            if not query: continue
            if query.lower() == 'exit': break
            
            output_data = {
                "original_query": query,
                "results": {}
            }

            # --- 1. Base TF-IDF (No PageRank, No Expansion) ---
            original_pr = indexer.pagerank
            indexer.pagerank = {} # Disable PR
            base_results = indexer.fused_search(query, top_n=5)
            indexer.pagerank = original_pr # Restore
            
            output_data["results"]["base_tfidf"] = []
            for res in base_results:
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["base_tfidf"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # --- 2. With PageRank (Link Analysis ON, No Expansion) ---
            pr_results = indexer.fused_search(query, top_n=5)
            output_data["results"]["with_pagerank"] = []
            for res in pr_results:
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["with_pagerank"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # --- 3. With Rocchio (Pseudo-Feedback Expansion) ---
            rel_docs = []
            for res in base_results[:3]: # Use top 3 from base as pseudo-feedback
                for d_id, url in indexer.url_map.items():
                    if url == res['url']: rel_docs.append(d_id); break
            
            expanded_rocchio = rocchio.expand(query, rel_docs, [])
            roc_query = query + " " + " ".join([t[0] for t in expanded_rocchio])
            output_data["expanded_query_rocchio"] = roc_query
            
            rocchio_results = indexer.fused_search(roc_query, top_n=5)
            output_data["results"]["with_rocchio"] = []
            for res in rocchio_results:
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["with_rocchio"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # --- 4. With Clustering (Association) ---
            word = query.split()[0].lower()
            assoc_terms = clusters.get_association_expansion(word, top_k=3)
            assoc_query = query + " " + " ".join([t[0] for t in assoc_terms])
            output_data["expanded_query_assoc"] = assoc_query
            output_data["results"]["cluster_association"] = []
            for res in indexer.fused_search(assoc_query, top_n=5):
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["cluster_association"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # --- 5. With Clustering (Metric) ---
            metric_terms = clusters.get_metric_expansion(word, top_k=3)
            metric_query = query + " " + " ".join([t[0] for t in metric_terms])
            output_data["expanded_query_metric"] = metric_query
            output_data["results"]["cluster_metric"] = []
            for res in indexer.fused_search(metric_query, top_n=5):
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["cluster_metric"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # --- 6. With Clustering (Scalar) ---
            scalar_terms = clusters.get_scalar_expansion(word, top_k=3)
            scalar_query = query + " " + " ".join([t[0] for t in scalar_terms])
            output_data["expanded_query_scalar"] = scalar_query
            output_data["results"]["cluster_scalar"] = []
            for res in indexer.fused_search(scalar_query, top_n=5):
                doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
                title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
                output_data["results"]["cluster_scalar"].append({
                    "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
                })

            # Save to JSON for Khushi
            with open("current_query_results.json", "w") as f:
                json.dump(output_data, f, indent=4)
            
            print(f"\n--- Results for: {query} ---")
            print(f"Rocchio Expansion: {roc_query}")
            print(f"Assoc Expansion:   {assoc_query}")
            print(f"Metric Expansion:  {metric_query}")
            print(f"Scalar Expansion:  {scalar_query}")
            print(f"Done! Results exported to 'current_query_results.json'")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_interactive()
