import os
import json
import pickle
import re
from collections import defaultdict
import math
from concurrent.futures import ProcessPoolExecutor

# This module implements the indexing and relevance scoring for the Predator search engine.
def process_single_file(args):
    path, stopwords = args
    local_index = defaultdict(int)
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read().lower()
            doc_id = os.path.basename(path)
            words = re.findall(r'\b[a-z]{3,}\b', text)
            for word in words:
                if word not in stopwords:
                    local_index[word] += 1
        return doc_id, local_index
    except Exception as e:
        return None, None

class PredatorIndexer:
    def __init__(self, pages_dir):
        self.pages_dir = pages_dir
        self.index_file = 'inverted_index.pkl'
        self.index = defaultdict(lambda: defaultdict(int))
        self.processed_files = set() 
        self.doc_count = 0 
        self.url_map = {}  # page_id.txt -> URL
        self.pagerank = {} # URL -> score
        self.stopwords = {"the", "a", "an", "and", "or", "but", "is", "in", "on", "at", "to", "for", "with"}

    def load_mapping(self, mapping_path):
        """Loads the JSONL mapping file provided by Sandeep"""
        print("Loading ID-to-URL mapping...")
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    # CLEANUP: Ensure the URL in the map is clean
                    self.url_map[f"page_{data['id']}.txt"] = data['url'].strip()
        print(f"Mapped {len(self.url_map)} file IDs to URLs.")

    def load_link_scores(self, scores_path):
        """Loads scores from link_analysis.py"""
        print("Loading PageRank scores...")
        if os.path.exists(scores_path):
            with open(scores_path, 'rb') as f:
                data = pickle.load(f)
                # CLEANUP: Lowercase all PageRank URLs so they match fused_search
                self.pagerank = {k.lower().strip(): v for k, v in data.get('pagerank', {}).items()}
        print(f"Loaded PageRank for {len(self.pagerank)} URLs.")

    def save_to_disk(self):
        data_to_save = {
            'index': {k: dict(v) for k, v in self.index.items()},
            'processed': self.processed_files,
            'doc_count': len(self.processed_files)
        }
        with open(self.index_file, 'wb') as f:
            pickle.dump(data_to_save, f)
        print(f"Index successfully saved to {self.index_file}")

    def load_from_disk(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as f:
                data = pickle.load(f)
                self.index = defaultdict(lambda: defaultdict(int), 
                                         {k: defaultdict(int, v) for k, v in data['index'].items()})
                self.processed_files = data['processed']
                self.doc_count = data.get('doc_count', len(self.processed_files))
            print(f"Loaded existing index with {len(self.processed_files)} files.")

    def run_incremental_indexing(self):
        self.load_from_disk()
        all_new_files = []
        for root, _, files in os.walk(self.pages_dir):
            for file in files:
                if file not in self.processed_files:
                    all_new_files.append((os.path.join(root, file), self.stopwords))

        if not all_new_files:
            print("No new files to add.")
            return

        print(f"Starting parallel indexing of {len(all_new_files)} files...")
        with ProcessPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(process_single_file, all_new_files))

        for doc_id, local_idx in results:
            if doc_id:
                self.processed_files.add(doc_id)
                for word, count in local_idx.items():
                    self.index[word][doc_id] = count

        self.doc_count = len(self.processed_files)
        self.save_to_disk()

    # This method combines TF-IDF and PageRank for final ranking of search results.
    def fused_search(self, query, top_n=10):
        """Combines TF-IDF and PageRank for final ranking"""
        query_terms = re.findall(r'\b[a-z]{3,}\b', query.lower())
        tfidf_scores = defaultdict(float)
        N = self.doc_count
        
        # 1. Calculate TF-IDF component
        for term in query_terms:
            if term in self.index:
                df = len(self.index[term])
                idf = math.log10(N / df) if df > 0 else 0
                for doc_id, freq in self.index[term].items():
                    tf = 1 + math.log10(freq)
                    tfidf_scores[doc_id] += (tf * idf)
        
        # 2. Add PageRank component (The Fusion)
        final_results = []
        num_query_terms = len(set(query_terms))
        seen_urls = set() # <--- ADDED: This keeps track of what we've already shown
        
        for doc_id, tf_score in tfidf_scores.items():
            # Get original URL to show on the UI, and a clean lowercase one for tracking
            original_url = self.url_map.get(doc_id, doc_id)
            clean_url = original_url.lower().strip()
            
            # <--- ADDED: If we have seen this exact URL already, skip to the next one!
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)
            
            pr_score = self.pagerank.get(clean_url, 0)
            
            # EXPONENTIAL COORDINATION FACTOR
            coord_factor = (len(coordination[doc_id]) / num_query_terms) ** 4
            
            # DEEP-LINK BOOSTING & NOISE FILTERING
            url_weight = 1.0
            
            # 2. Penalty for Homepages (too broad)
            if clean_url.count("/") <= 3: # e.g., http://fnai.org/ or http://fnai.org/home
                url_weight *= 0.3
                
            # 3. Boost for "Deep" content pages
            if clean_url.count("/") >= 5: # e.g., http://fnai.org/species/animals/panther.php
                url_weight *= 2.0
            
            total_score = (tf_score + (pr_score * 1000)) * coord_factor * url_weight
            
            if total_score > 0:
                final_results.append({
                    "url": original_url,  # Keep the original casing for Khushi's UI
                    "score": total_score,
                    "tf_idf": tf_score,
                    "coordination": coord_factor,
                    "page_rank": pr_score
                })
        
        return sorted(final_results, key=lambda x: x['score'], reverse=True)[:top_n]


if __name__ == "__main__":
    # 1. Initialize and load your saved data
    engine = PredatorIndexer(os.path.join('data', 'pages'))
    engine.load_from_disk()
    engine.load_mapping(os.path.join('data', 'url_mapping.jsonl'))
    engine.load_link_scores('link_analysis_scores.pkl')

    # 2. Run the exact query Khushi tested
    test_query = "african lion"
    print(f"\n--- Testing Query: '{test_query}' ---")
    print(f"Index size: {len(engine.index)} terms")
    results = engine.fused_search(test_query, top_n=5)

    # 3. Print the exact scores the UI is getting
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['url']}")
        print(f"   Hybrid Score: {res['score']:.4f} | VSM (TF-IDF): {res['tf_idf']:.4f}\n")
