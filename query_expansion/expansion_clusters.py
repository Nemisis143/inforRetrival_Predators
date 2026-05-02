import os
import sys
import numpy as np
from collections import defaultdict
import math
import functools

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer

class ClusterExpander:
    def __init__(self, indexer):
        self.indexer = indexer
        self.forward_index = defaultdict(dict)
        self.term_norms = {} 
        self.term_dfs = {} # Store document frequency for noise filtering
        
        # Noise threshold: ignore terms that appear in more than 1% of the collection
        self.max_df = self.indexer.doc_count * 0.01 
        
        self._initialize_structures()

    def _initialize_structures(self):
        print("Optimizing Cluster Engine: Building Forward Index and Norms...", end="", flush=True)
        for term, postings in self.indexer.index.items():
            df = len(postings)
            self.term_dfs[term] = df
            
            # Skip stopwords and ultra-common words from the forward index to save memory and noise
            if term in self.indexer.stopwords or df > self.max_df or len(term) < 3:
                continue
                
            norm = sum(f**2 for f in postings.values())
            self.term_norms[term] = norm
            
            for doc_id, freq in postings.items():
                self.forward_index[doc_id][term] = freq
        print(" Done!", flush=True)

    def _get_idf(self, term):
        df = self.term_dfs.get(term, 0)
        if df == 0: return 0
        return math.log10(self.indexer.doc_count / df)

    @functools.lru_cache(maxsize=100)
    def _get_weighted_co_occurrences(self, query_term):
        """
        Calculates IDF-weighted co-occurrences.
        """
        if query_term not in self.indexer.index:
            return {}, 0
            
        postings_u = self.indexer.index[query_term]
        c_uv = defaultdict(float)
        
        # c_uu is the pre-calculated norm for the query term
        c_uu = self.term_norms.get(query_term, 0)
        if c_uu == 0: # If query term itself was filtered as noise/stopword
            c_uu = sum(f**2 for f in postings_u.values())
        
        for doc_id, f_u in postings_u.items():
            doc_content = self.forward_index.get(doc_id, {})
            for v_term, f_v in doc_content.items():
                if v_term != query_term:
                    # Weight by IDF of the target term to prefer meaningful words over 'google/from'
                    # Even if 'from' wasn't a stopword, its low IDF would sink its score
                    idf_v = self._get_idf(v_term)
                    c_uv[v_term] += (f_u * f_v * idf_v)
        
        return dict(c_uv), c_uu

    def get_association_expansion(self, query_term, top_k=5):
        c_uv, _ = self._get_weighted_co_occurrences(query_term)
        results = sorted(c_uv.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_metric_expansion(self, query_term, top_k=5):
        c_uv, c_uu = self._get_weighted_co_occurrences(query_term)
        scores = []
        for v_term, val_uv in c_uv.items():
            c_vv = self.term_norms.get(v_term, 0)
            if c_vv > 0:
                similarity = val_uv / (c_uu + c_vv - val_uv)
                scores.append((v_term, similarity))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def get_scalar_expansion(self, query_term, top_k=5):
        c_uv, c_uu = self._get_weighted_co_occurrences(query_term)
        u_norm = math.sqrt(c_uu)
        if u_norm == 0: return []
        
        scores = []
        for v_term, val_uv in c_uv.items():
            c_vv = self.term_norms.get(v_term, 0)
            v_norm = math.sqrt(c_vv)
            if v_norm > 0:
                similarity = val_uv / (u_norm * v_norm)
                scores.append((v_term, similarity))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
