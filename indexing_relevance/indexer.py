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
                    # Maps "page_1.txt" to its URL
                    self.url_map[f"page_{data['id']}.txt"] = data['url']
        print(f"Mapped {len(self.url_map)} file IDs to URLs.")

    def load_link_scores(self, scores_path):
        """Loads scores from link_analysis.py"""
        print("Loading PageRank scores...")
        if os.path.exists(scores_path):
            with open(scores_path, 'rb') as f:
                data = pickle.load(f)
                self.pagerank = data.get('pagerank', {})
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
    def get_doc_vectors(self):
        """Generates TF-IDF document vectors for the clustering module (Praneeth)"""
        doc_vectors = defaultdict(dict)
        N = self.doc_count
        for term, postings in self.index.items():
            df = len(postings)
            idf = math.log10(N / df) if df > 0 else 0
            for doc_id, freq in postings.items():
                tf = 1 + math.log10(freq)
                # Maps back to the actual URL if possible
                url = self.url_map.get(doc_id, doc_id) 
                doc_vectors[url][term] = tf * idf
        return doc_vectors
    
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
        for doc_id, tf_score in tfidf_scores.items():
            url = self.url_map.get(doc_id)
            pr_score = self.pagerank.get(url, 0)
            
            # Weighting: TF-IDF + (PageRank * weight)
            # We use a weight of 1000 because PR values are tiny decimals
            total_score = tf_score + (pr_score * 1000)
            
            final_results.append({
                "url": url if url else doc_id,
                "score": total_score,
                "tf_idf": tf_score,
                "page_rank": pr_score
            })
        
        return sorted(final_results, key=lambda x: x['score'], reverse=True)[:top_n]

# Example usage
if __name__ == "__main__":
    # Paths
    PAGES_PATH = os.path.join('data', 'pages')
    MAPPING_PATH = os.path.join('data', 'url_mapping.jsonl')
    SCORES_PATH = 'link_analysis_scores.pkl'
    
    search_engine = PredatorIndexer(PAGES_PATH)
    
    # Run/Load Index
    search_engine.run_incremental_indexing()
    
    # Load Fusion Data
    search_engine.load_mapping(MAPPING_PATH)
    search_engine.load_link_scores(SCORES_PATH)
    
    # Final Test
    query = "lion"
    print(f"\n--- Fused Search Results for: '{query}' ---")
    results = search_engine.fused_search(query)
    
    for i, res in enumerate(results, 1):
        print(f"{i}. {res['url']}")
        print(f"   [Final Score: {res['score']:.4f}] (TF-IDF: {res['tf_idf']:.2f}, PR: {res['page_rank']:.6f})")