# # from flask import Flask, request, jsonify, render_template
# # import requests

# # app = Flask(__name__)

# # # ✅ PUT YOUR FUNCTION HERE (top or bottom — both fine)
# # def get_our_results(query):
# #     return [{"title": "Sample Result", "link": "https://example.com"}]


# # def get_cluster_results(query):
# #     return [{"title": "Cluster Result", "link": "#"}]


# # def get_expanded_results(query):
# #     return [{"title": "Expanded Result", "link": "#"}]

# # def get_google_results(query):
# #     API_KEY = "AIzaSyDlIW0d2rdMsroVo_cTljTDX0y4JL2aGKI"
# #     CX = "91b2e228fce9f4279"

# #     url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"

# #     res = requests.get(url).json()

# #     print("FULL GOOGLE RESPONSE:", res)  # 👈 ADD THIS

# #     results = []

# #     for item in res.get("items", []):
# #         results.append({
# #             "title": item["title"],
# #             "link": item["link"]
# #         })

# #     return results




# from flask import Flask, request, jsonify, render_template
# import requests
# import os
# import pickle
# from indexer import PredatorIndexer

# app = Flask(__name__)

# # ── Load the search engine once at startup ──
# PAGES_PATH   = os.path.join('data', 'pages')
# MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
# SCORES_PATH  = 'link_analysis_scores.pkl'

# engine = PredatorIndexer(PAGES_PATH)
# engine.load_from_disk()          # loads inverted_index.pkl
# engine.load_mapping(MAPPING_PATH)
# engine.load_link_scores(SCORES_PATH)
# print("Search engine loaded ✓")

# # ✅ PUT YOUR FUNCTION HERE (top or bottom — both fine)
# def get_our_results(query, model="vsm"):
#     try:
#         raw = engine.fused_search(query, top_n=10)
#         return [
#             {
#                 "title":     r.get("url", ""),
#                 "link":      r.get("url", "#"),
#                 "snippet":   f"TF-IDF: {r.get('tf_idf', 0):.2f} | PageRank: {r.get('page_rank', 0):.6f}",
#                 "score":     r.get("score", 0)
#             }
#             for r in raw
#         ]
#     except Exception as e:
#         print(f"fused_search error: {e}")
#         return []


# def get_cluster_results(query):
#     return [{"title": "Cluster Result", "link": "#"}]


# def get_expanded_results(query):
#     return [{"title": "Expanded Result", "link": "#"}]

# # def get_google_results(query):
# #     API_KEY = "AIzaSyDlIW0d2rdMsroVo_cTljTDX0y4JL2aGKI"
# #     CX = "91b2e228fce9f4279"

# #     url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"

# #     res = requests.get(url).json()

# #     print("FULL GOOGLE RESPONSE:", res)  # 👈 ADD THIS

# #     results = []

# #     for item in res.get("items", []):
# #         results.append({
# #             "title": item["title"],
# #             "link": item["link"]
# #         })

# #     return results




# def get_google_results(query: str, num: int = 10) -> dict:
#     api_key = "2141d55b54e69a1a5f73f00550873341857b4d64c21cc8c7ba3ad387a6715b50"  # free at serpapi.com
#     params = {
#         "q": query,
#         "num": num,
#         "api_key": api_key,
#         "engine": "google"
#     }
#     resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
#     data = resp.json()

#     return [
#     {
#         "title": r.get("title"),
#         "link":  r.get("link"),      # ← change "url" to "link"
#         "snippet": r.get("snippet", "")
#     }
#     for r in data.get("organic_results", [])[:num]
#     ]

# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/search", methods=["POST"])
# def search():
#     body  = request.json
#     query = body.get("query", "")
#     model = body.get("model", "vsm")

#     # ✅ CALLING YOUR FUNCTION HERE
#     our_results = get_our_results(query, model),
#     cluster_results = get_cluster_results(query)
#     expanded_results = get_expanded_results(query)
#     google_results = get_google_results(query)

#     return jsonify({
#         "our_results": our_results,
#         "cluster_results": cluster_results,
#         "expanded_results": expanded_results,
#         "google_results": google_results,
#         "bing_results": []
#     })


# app.run(debug=True)
# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/search", methods=["POST"])
# def search():
#     query = request.json["query"]

#     # ✅ CALLING YOUR FUNCTION HERE
#     our_results = get_our_results(query)
#     cluster_results = get_cluster_results(query)
#     expanded_results = get_expanded_results(query)
#     google_results = get_google_results(query)

#     return jsonify({
#         "our_results": our_results,
#         "cluster_results": cluster_results,
#         "expanded_results": expanded_results,
#         "google_results": google_results,
#         "bing_results": []
#     })


# app.run(debug=True)









## option 1
# from flask import Flask, request, jsonify, render_template
# import requests
# import os
# import pickle
# from indexer import PredatorIndexer

# app = Flask(__name__)

# # ── Load the search engine once at startup ──
# PAGES_PATH   = os.path.join('data', 'pages')
# MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
# SCORES_PATH  = 'link_analysis_scores.pkl'

# engine = PredatorIndexer(PAGES_PATH)
# engine.load_from_disk()
# engine.load_mapping(MAPPING_PATH)
# engine.load_link_scores(SCORES_PATH)
# print("Search engine loaded ✓")


# def get_our_results(query, model="vsm"):
#     try:
#         raw = engine.fused_search(query, top_n=10)
#         return [
#             {
#                 "title":   r.get("url", ""),
#                 "link":    r.get("url", "#"),
#                 "snippet": f"TF-IDF: {r.get('tf_idf', 0):.2f} | PageRank: {r.get('page_rank', 0):.6f}",
#                 "score":   r.get("score", 0)
#             }
#             for r in raw
#         ]
#     except Exception as e:
#         print(f"fused_search error: {e}")
#         return []


# def get_cluster_results(query):
#     # TODO: replace with Praneeth's clustering module
#     # Expected return format:
#     # [
#     #   {
#     #     "cluster_id": 0,
#     #     "label": "Cluster Label",
#     #     "documents": [{"title": "...", "link": "...", "snippet": "..."}]
#     #   }
#     # ]
#     return []


# def get_expanded_results(query, method="rocchio"):
#     # TODO: replace with Tanvi's query expansion module
#     # Expected return format:
#     # {
#     #   "expanded_query": "original + new terms",
#     #   "results": [{"title": "...", "link": "...", "snippet": "..."}]
#     # }
#     return {"expanded_query": "", "results": []}


# def get_google_results(query, num=10):
#     api_key = "2141d55b54e69a1a5f73f00550873341857b4d64c21cc8c7ba3ad387a6715b50"
#     params = {
#         "q":       query,
#         "num":     num,
#         "api_key": api_key,
#         "engine":  "google"
#     }
#     try:
#         resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
#         data = resp.json()
#         return [
#             {
#                 "title":   r.get("title"),
#                 "link":    r.get("link"),
#                 "snippet": r.get("snippet", "")
#             }
#             for r in data.get("organic_results", [])[:num]
#         ]
#     except Exception as e:
#         print(f"Google results error: {e}")
#         return []


# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/search", methods=["POST"])
# def search():
#     body      = request.json
#     query     = body.get("query", "")
#     model     = body.get("model", "vsm")
#     expansion = body.get("expansion", "rocchio")

#     our_results      = get_our_results(query, model)
#     cluster_results  = get_cluster_results(query)
#     expansion_data   = get_expanded_results(query, expansion)
#     google_results   = get_google_results(query)

#     return jsonify({
#         "our_results":      our_results,
#         "cluster_results":  cluster_results,
#         "expanded_query":   expansion_data["expanded_query"],
#         "expanded_results": expansion_data["results"],
#         "google_results":   google_results,
#         "bing_results":     []
#     })


# if __name__ == "__main__":
#     app.run(debug=True)

## AFTER NIKITA CODE
# from flask import Flask, request, jsonify, render_template
# import requests
# import os
# import pickle
# import math
# import re
# from collections import defaultdict
# from indexer import PredatorIndexer

# app = Flask(__name__)

# # ── Load the search engine once at startup ──
# PAGES_PATH   = os.path.join('data', 'pages')
# MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
# SCORES_PATH  = 'link_analysis_scores.pkl'

# engine = PredatorIndexer(PAGES_PATH)
# engine.load_from_disk()
# engine.load_mapping(MAPPING_PATH)
# engine.load_link_scores(SCORES_PATH)

# # Load HITS scores separately (saved in same pkl)
# hits_hubs = {}
# hits_authorities = {}
# if os.path.exists(SCORES_PATH):
#     with open(SCORES_PATH, 'rb') as f:
#         scores_data = pickle.load(f)
#         hits_hubs        = scores_data.get('hubs', {})
#         hits_authorities = scores_data.get('authorities', {})

# print("Search engine loaded ✓")


# def get_our_results(query, model="vsm"):
#     try:
#         query_terms = re.findall(r'\b[a-z]{3,}\b', query.lower())
#         N = engine.doc_count

#         # Step 1: Calculate TF-IDF scores for all matching docs
#         tfidf_scores = defaultdict(float)
#         for term in query_terms:
#             if term in engine.index:
#                 df = len(engine.index[term])
#                 idf = math.log10(N / df) if df > 0 else 0
#                 for doc_id, freq in engine.index[term].items():
#                     tf = 1 + math.log10(freq)
#                     tfidf_scores[doc_id] += (tf * idf)

#         # Step 2: Score based on selected model
#         final_results = []
#         for doc_id, tf_score in tfidf_scores.items():
#             url = engine.url_map.get(doc_id, doc_id)
#             pr_score   = engine.pagerank.get(url, 0)
#             hub_score  = hits_hubs.get(url, 0)
#             auth_score = hits_authorities.get(url, 0)

#             if model == "vsm":
#                 score = tf_score

#             elif model == "pagerank":
#                 # PageRank only -- ignore TF-IDF
#                 score = pr_score * 1000

#             elif model == "hits":
#                 # Use authority score -- pages authoritative on this topic
#                 score = auth_score * 1000

#             elif model == "combined":
#                 # Hybrid: TF-IDF + PageRank + Authority
#                 score = tf_score + (pr_score * 1000) + (auth_score * 500)

#             else:
#                 score = tf_score

#             final_results.append({
#                 "title":   url,
#                 "link":    url,
#                 "snippet": f"TF-IDF: {tf_score:.2f} | PageRank: {pr_score:.6f} | Authority: {auth_score:.6f}",
#                 "score":   score
#             })

#         # Sort and return top 10
#         final_results.sort(key=lambda x: x['score'], reverse=True)
#         return final_results[:10]

#     except Exception as e:
#         print(f"get_our_results error: {e}")
#         return []


# def get_cluster_results(query):
#     # TODO: plug in Praneeth's clustering module
#     return []


# def get_expanded_results(query, method="rocchio"):
#     # TODO: plug in Tanvi's query expansion module
#     return {"expanded_query": "", "results": []}


# def get_google_results(query, num=10):
#     api_key = "2141d55b54e69a1a5f73f00550873341857b4d64c21cc8c7ba3ad387a6715b50"
#     params = {
#         "q":       query,
#         "num":     num,
#         "api_key": api_key,
#         "engine":  "google"
#     }
#     try:
#         resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
#         data = resp.json()
#         return [
#             {
#                 "title":   r.get("title"),
#                 "link":    r.get("link"),
#                 "snippet": r.get("snippet", "")
#             }
#             for r in data.get("organic_results", [])[:num]
#         ]
#     except Exception as e:
#         print(f"Google results error: {e}")
#         return []


# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/search", methods=["POST"])
# def search():
#     body      = request.json
#     query     = body.get("query", "")
#     model     = body.get("model", "vsm")
#     expansion = body.get("expansion", "rocchio")

#     our_results     = get_our_results(query, model)
#     cluster_results = get_cluster_results(query)
#     expansion_data  = get_expanded_results(query, expansion)
#     google_results  = get_google_results(query)

#     return jsonify({
#         "our_results":      our_results,
#         "cluster_results":  cluster_results,
#         "expanded_query":   expansion_data["expanded_query"],
#         "expanded_results": expansion_data["results"],
#         "google_results":   google_results,
#         "bing_results":     []
#     })


# if __name__ == "__main__":
#     app.run(debug=True)

## TANVI 

# from flask import Flask, request, jsonify, render_template
# import requests
# import os
# import sys
# import math
# import re
# import pickle
# from collections import defaultdict

# sys.path.append(os.path.join(os.path.dirname(__file__), 'query_expansion'))

# from indexer import PredatorIndexer
# from query_expansion.rocchio import RocchioExpander
# from query_expansion.expansion_clusters import ClusterExpander

# app = Flask(__name__)

# PAGES_PATH   = os.path.join('data', 'pages')
# MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
# SCORES_PATH  = 'link_analysis_scores.pkl'

# print("Loading search engine...")
# engine = PredatorIndexer(PAGES_PATH)
# engine.load_from_disk()
# engine.load_mapping(MAPPING_PATH)
# engine.load_link_scores(SCORES_PATH)

# # Load HITS scores at startup
# hits_authorities = {}
# if os.path.exists(SCORES_PATH):
#     with open(SCORES_PATH, 'rb') as f:
#         scores_data = pickle.load(f)
#         hits_authorities = scores_data.get('authorities', {})

# print("Loading query expansion modules...")
# rocchio  = RocchioExpander(engine)
# clusters = ClusterExpander(engine)
# print("All modules loaded ✓")


# def get_doc_metadata(doc_id):
#     path = os.path.join(PAGES_PATH, doc_id)
#     title   = engine.url_map.get(doc_id, doc_id)
#     snippet = ""
#     if os.path.exists(path):
#         try:
#             with open(path, 'r', encoding='utf-8', errors='ignore') as f:
#                 content = f.read().strip()
#                 lines = [l.strip() for l in content.split('\n') if l.strip()]
#                 if lines:
#                     title   = lines[0][:100]
#                     snippet = " ".join(lines)[:200] + "..."
#         except:
#             pass
#     return title, snippet


# # def get_our_results(query, model="vsm"):
# #     try:
# #         if model == "pagerank":
# #             # Temporarily boost pagerank weight
# #             raw = engine.fused_search(query, top_n=10)
# #         elif model == "hits":
# #             raw = engine.fused_search(query, top_n=10)
# #         else:
# #             raw = engine.fused_search(query, top_n=10)

# #         results = []
# #         for res in raw:
# #             doc_id = next((d for d, u in engine.url_map.items() if u == res['url']), None)
# #             title, snippet = get_doc_metadata(doc_id) if doc_id else (res['url'], "")
# #             results.append({
# #                 "title":   title,
# #                 "link":    res['url'],
# #                 "snippet": snippet,
# #                 "score":   round(res['score'], 4)
# #             })
# #         return results
# #     except Exception as e:
# #         print(f"get_our_results error: {e}")
# #         return []

# def get_our_results(query, model="vsm"):
#     try:
#         if model == "vsm":
#             # Pure TF-IDF, no PageRank
#             original_pr = engine.pagerank
#             engine.pagerank = {}
#             raw = engine.fused_search(query, top_n=10)
#             engine.pagerank = original_pr
#         else:
#             # Hybrid/PageRank/HITS -- use full fused_search
#             raw = engine.fused_search(query, top_n=10)

#         results = []
#         for res in raw:
#             doc_id = next((d for d, u in engine.url_map.items() if u == res['url']), None)
#             title, snippet = get_doc_metadata(doc_id) if doc_id else (res['url'], "")
#             results.append({
#                 "title":   title,
#                 "link":    res['url'],
#                 "snippet": snippet,
#                 "score":   round(res['score'], 4)
#             })
#         return results
#     except Exception as e:
#         print(f"get_our_results error: {e}")
#         return []

# def get_expanded_results(query, method="rocchio"):
#     try:
#         resp = requests.get(f"http://127.0.0.1:5001/search?q={query}", timeout=30)
#         data = resp.json()
        
#         method_map = {
#             "rocchio":     ("expanded_query_rocchio", "with_rocchio"),
#             "association": ("expanded_query_assoc",   "cluster_association"),
#             "metric":      ("expanded_query_metric",  "cluster_metric"),
#             "scalar":      ("expanded_query_scalar",  "cluster_scalar"),
#         }
        
#         eq_key, results_key = method_map.get(method, ("expanded_query_rocchio", "with_rocchio"))
#         expanded_query = data.get(eq_key, query)
#         raw = data.get("results", {}).get(results_key, [])
        
#         results = [
#             {"title": r.get("title"), "link": r.get("url"), "snippet": r.get("snippet"), "score": r.get("score")}
#             for r in raw
#         ]
#         return {"expanded_query": expanded_query, "results": results}
#     except Exception as e:
#         print(f"Expansion API error: {e}")
#         return {"expanded_query": query, "results": []}


# def get_cluster_results(query):
#     # TODO: plug in Praneeth's clustering module
#     return []


# def get_google_results(query, num=10):
#     api_key = "2141d55b54e69a1a5f73f00550873341857b4d64c21cc8c7ba3ad387a6715b50"
#     params  = {"q": query, "num": num, "api_key": api_key, "engine": "google"}
#     try:
#         resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
#         data = resp.json()
#         return [
#             {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet", "")}
#             for r in data.get("organic_results", [])[:num]
#         ]
#     except Exception as e:
#         print(f"Google results error: {e}")
#         return []


# @app.route("/")
# def home():
#     return render_template("index.html")


# @app.route("/search", methods=["POST"])
# def search():
#     body      = request.json
#     query     = body.get("query", "")
#     model     = body.get("model", "vsm")
#     expansion = body.get("expansion", "rocchio")

#     our_results     = get_our_results(query, model)
#     cluster_results = get_cluster_results(query)
#     expansion_data  = get_expanded_results(query, expansion)
#     google_results  = get_google_results(query)

#     return jsonify({
#         "our_results":      our_results,
#         "cluster_results":  cluster_results,
#         "expanded_query":   expansion_data["expanded_query"],
#         "expanded_results": expansion_data["results"],
#         "google_results":   google_results,
#         "bing_results":     []
#     })


# if __name__ == "__main__":
#     app.run(debug=True)

#### NIKITA

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