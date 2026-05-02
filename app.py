from flask import Flask, request, jsonify, render_template
import requests
import os
import sys
import pickle

sys.path.append(os.path.join(os.path.dirname(__file__), 'query_expansion'))

from indexer import PredatorIndexer
from query_expansion.rocchio import RocchioExpander
from query_expansion.expansion_clusters import ClusterExpander

app = Flask(__name__)

PAGES_PATH   = os.path.join('data', 'pages')
MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
SCORES_PATH  = 'link_analysis_scores.pkl'

print("Loading search engine...")
engine = PredatorIndexer(PAGES_PATH)
engine.load_from_disk()
engine.load_mapping(MAPPING_PATH)
engine.load_link_scores(SCORES_PATH)

print("Loading query expansion modules...")
rocchio  = RocchioExpander(engine)
clusters = ClusterExpander(engine)
print("All modules loaded ✓")


def get_doc_metadata(doc_id):
    path = os.path.join(PAGES_PATH, doc_id)
    title   = engine.url_map.get(doc_id, doc_id)
    snippet = ""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                if lines:
                    title   = lines[0][:100]
                    snippet = " ".join(lines)[:200] + "..."
        except:
            pass
    return title, snippet


def get_our_results(query, model="vsm"):
    try:
        if model == "vsm":
            raw = engine.fused_search(query, top_n=10, mode='vsm')
        else:
            raw = engine.fused_search(query, top_n=10, mode='hybrid')

        results = []
        for res in raw:
            doc_id = next((d for d, u in engine.url_map.items() if u == res['url']), None)
            title, snippet = get_doc_metadata(doc_id) if doc_id else (res['url'], "")
            results.append({
                "title":   title,
                "link":    res['url'],
                "snippet": snippet,
                "score":   round(res['score'] if model != "vsm" else res['tf_idf'], 4)
            })
        return results
    except Exception as e:
        print(f"get_our_results error: {e}")
        return []


def get_expanded_results(query, method="rocchio"):
    try:
        resp = requests.get(f"http://127.0.0.1:5001/search?q={query}", timeout=30)
        data = resp.json()

        method_map = {
            "rocchio":     ("expanded_query_rocchio", "with_rocchio"),
            "association": ("expanded_query_assoc",   "cluster_association"),
            "metric":      ("expanded_query_metric",  "cluster_metric"),
            "scalar":      ("expanded_query_scalar",  "cluster_scalar"),
        }

        eq_key, results_key = method_map.get(method, ("expanded_query_rocchio", "with_rocchio"))
        expanded_query = data.get(eq_key, query)
        raw = data.get("results", {}).get(results_key, [])

        results = [
            {"title": r.get("title"), "link": r.get("url"), "snippet": r.get("snippet"), "score": r.get("score")}
            for r in raw
        ]
        return {"expanded_query": expanded_query, "results": results}
    except Exception as e:
        print(f"Expansion API error: {e}")
        return {"expanded_query": query, "results": []}


def get_cluster_results(query):
    # TODO: plug in Praneeth's clustering module
    return []


def get_google_results(query, num=10):
    api_key = "2141d55b54e69a1a5f73f00550873341857b4d64c21cc8c7ba3ad387a6715b50"
    params  = {"q": query, "num": num, "api_key": api_key, "engine": "google"}
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = resp.json()
        return [
            {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", [])[:num]
        ]
    except Exception as e:
        print(f"Google results error: {e}")
        return []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    body      = request.json
    query     = body.get("query", "")
    model     = body.get("model", "vsm")
    expansion = body.get("expansion", "rocchio")

    our_results     = get_our_results(query, model)
    cluster_results = get_cluster_results(query)
    expansion_data  = get_expanded_results(query, expansion)
    google_results  = get_google_results(query)

    return jsonify({
        "our_results":      our_results,
        "cluster_results":  cluster_results,
        "expanded_query":   expansion_data["expanded_query"],
        "expanded_results": expansion_data["results"],
        "google_results":   google_results,
        "bing_results":     []
    })


if __name__ == "__main__":
    app.run(debug=False)