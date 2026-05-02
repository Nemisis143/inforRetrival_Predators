import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer
from query_expansion.rocchio import RocchioExpander
from query_expansion.expansion_clusters import ClusterExpander

app = Flask(__name__)
CORS(app) # This allows the frontend to access the API

# Global variables to hold the loaded engine
indexer = None
rocchio = None
clusters = None

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

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    print(f"Processing query: {query}")
    
    output_data = {
        "original_query": query,
        "results": {}
    }

    # --- 1. Base TF-IDF ---
    original_pr = indexer.pagerank
    indexer.pagerank = {} 
    base_results = indexer.fused_search(query, top_n=5)
    indexer.pagerank = original_pr 
    
    output_data["results"]["base_tfidf"] = []
    for res in base_results:
        doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
        title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
        output_data["results"]["base_tfidf"].append({
            "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
        })

    # --- 2. With PageRank ---
    pr_results = indexer.fused_search(query, top_n=5)
    output_data["results"]["with_pagerank"] = []
    for res in pr_results:
        doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
        title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
        output_data["results"]["with_pagerank"].append({
            "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
        })

    # --- 3. With Rocchio ---
    rel_docs = []
    for res in base_results[:3]:
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
    output_data["results"]["cluster_association"] = []
    output_data["expanded_query_assoc"] = assoc_query
    for res in indexer.fused_search(assoc_query, top_n=5):
        doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
        title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
        output_data["results"]["cluster_association"].append({
            "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
        })

    # --- 5. With Clustering (Metric) ---
    metric_terms = clusters.get_metric_expansion(word, top_k=3)
    metric_query = query + " " + " ".join([t[0] for t in metric_terms])
    output_data["results"]["cluster_metric"] = []
    output_data["expanded_query_metric"] = metric_query
    for res in indexer.fused_search(metric_query, top_n=5):
        doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
        title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
        output_data["results"]["cluster_metric"].append({
            "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
        })

    # --- 6. With Clustering (Scalar) ---
    scalar_terms = clusters.get_scalar_expansion(word, top_k=3)
    scalar_query = query + " " + " ".join([t[0] for t in scalar_terms])
    output_data["results"]["cluster_scalar"] = []
    output_data["expanded_query_scalar"] = scalar_query
    for res in indexer.fused_search(scalar_query, top_n=5):
        doc_id = next((d for d, u in indexer.url_map.items() if u == res['url']), None)
        title, snippet = get_doc_metadata(doc_id, "data/pages") if doc_id else (res['url'], "")
        output_data["results"]["cluster_scalar"].append({
            "url": res['url'], "title": title, "snippet": snippet, "score": round(res['score'], 4)
        })

    return jsonify(output_data)

if __name__ == "__main__":
    print("\n--- Initializing Predator Search API ---")
    print("Loading index (takes ~35s)...")
    
    indexer = PredatorIndexer("data/pages")
    indexer.load_from_disk()
    indexer.load_mapping("data/url_mapping.jsonl")
    indexer.load_link_scores("link_analysis_scores.pkl")
    
    rocchio = RocchioExpander(indexer)
    clusters = ClusterExpander(indexer)
    
    print("\n--- API IS LIVE ON http://127.0.0.1:5000 ---")
    app.run(port=5000, debug=False)
