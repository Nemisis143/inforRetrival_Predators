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
        self.doc_lengths = {} 
        self.stopwords = {"the", "a", "an", "and", "or", "but", "is", "in", "on", "at", "to", "for", "with"}

    def load_mapping(self, mapping_path):
        print("Loading ID-to-URL mapping...")
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    self.url_map[f"page_{data['id']}.txt"] = data['url']
        print(f"Mapped {len(self.url_map)} file IDs to URLs.")

    def load_link_scores(self, scores_path):
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
            'doc_count': len(self.processed_files),
            'doc_lengths': self.doc_lengths
        }
        with open(self.index_file, 'wb') as f:
            pickle.dump(data_to_save, f)

    def load_from_disk(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as f:
                data = pickle.load(f)
                self.index = defaultdict(lambda: defaultdict(int), 
                                         {k: defaultdict(int, v) for k, v in data['index'].items()})
                self.processed_files = data['processed']
                self.doc_count = data.get('doc_count', len(self.processed_files))
                self.doc_lengths = data.get('doc_lengths', {})
            
            if not self.doc_lengths and self.index:
                print("One-time optimization: Calculating document lengths...")
                for term, postings in self.index.items():
                    for doc_id, freq in postings.items():
                        self.doc_lengths[doc_id] = self.doc_lengths.get(doc_id, 0) + freq
            print(f"Loaded existing index with {len(self.processed_files)} files.")

    def fused_search(self, query, top_n=10):
        """Combines Length-Normalized TF-IDF, PageRank, and Deep-Link Boosting"""
        raw_query_terms = re.findall(r'\b[a-z]{3,}\b', query.lower())
        query_terms = [t for t in raw_query_terms if t not in self.stopwords]
        if not query_terms: query_terms = raw_query_terms
            
        tfidf_scores = defaultdict(float)
        coordination = defaultdict(set)
        N = self.doc_count
        avg_doc_len = sum(self.doc_lengths.values()) / N if self.doc_lengths else 1000
        
        for i, term in enumerate(query_terms):
            if term in self.index:
                df = len(self.index[term])
                idf = math.log10(N / df) if df > 0 else 0
                w_q = idf * (5.0 if i < 2 else 1.0)
                
                for doc_id, freq in self.index[term].items():
                    doc_len = self.doc_lengths.get(doc_id, avg_doc_len)
                    norm_factor = 0.1 + 0.9 * (doc_len / avg_doc_len)
                    tf_d = (freq / norm_factor)
                    tfidf_scores[doc_id] += (w_q * tf_d)
                    coordination[doc_id].add(term)
        
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