import os
import sys
import numpy as np
from collections import defaultdict
import math
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer

class RocchioExpander:
    def __init__(self, indexer, alpha=1.0, beta=0.4, gamma=0.1):
        self.indexer = indexer
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.num_docs = self.indexer.doc_count
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        self.min_df = 3 

    def _get_lift_exc(self, term, theme):
        term_postings = self.indexer.index.get(term, {})
        df_term = len(term_postings)
        if df_term == 0: return 0, 0
        theme_docs = set(self.indexer.index.get(theme, {}).keys())
        if not theme_docs: return 0, 0
        intersection_count = len(set(term_postings.keys()) & theme_docs)
        if intersection_count == 0: return 0, 0
        exclusivity = intersection_count / df_term
        popularity_in_theme = intersection_count / len(theme_docs)
        global_popularity = df_term / self.num_docs
        lift = popularity_in_theme / global_popularity if global_popularity > 0 else 0
        return exclusivity, lift


    def _get_query_bias(self, term, query_tokens, rel_centroid=None):
        """
        Calculates Specificity Lift for a term using query tokens and the relevant centroid.
        Prevents generic words from dominating by using exclusivity and lift.
        """
        term_postings = self.indexer.index.get(term, {})
        if len(term_postings) < self.min_df: return 0.01

        pos_score = 0.1
        
        if query_tokens:
            query_signal = 0
            for t in query_tokens:
                exc, lift = self._get_lift_exc(term, t)
                query_signal += exc * math.log10(1 + lift)
            pos_score += query_signal / len(query_tokens)
            
        if rel_centroid:
            top_terms = sorted(rel_centroid.items(), 
                              key=lambda x: x[1], reverse=True)[:10]
            centroid_signal = 0
            for theme, weight in top_terms:
                exc, lift = self._get_lift_exc(term, theme)
                centroid_signal += weight * (exc * math.log10(1 + lift))
            pos_score += centroid_signal / len(top_terms)
                
        return max(0.01, pos_score)

    def _get_idf(self, term):
        df = len(self.indexer.index.get(term, {}))
        if df < self.min_df: return 0 
        raw_idf = math.log10(self.num_docs / df)
        return min(raw_idf, 3.0)

    def _get_query_vector(self, query):
        tokens = query.lower().split()
        tf_dict = defaultdict(int)
        for t in tokens: 
            if t not in self.stop_words:
                tf_dict[self.stemmer.stem(t)] += 1
            
        vector = defaultdict(float)
        for term, freq in tf_dict.items():
            scaled_tf = 1 + math.log10(freq)
            vector[term] = scaled_tf * self._get_idf(term)
        return self._normalize(vector)

    def _normalize(self, vector):
        if not vector: return vector
        norm = math.sqrt(sum(val**2 for val in vector.values()))
        if norm == 0: return vector
        return {term: val / norm for term, val in vector.items()}

    def _is_trustworthy_rel_doc(self, doc_id, query_stems, doc_vectors):
        """
        Returns True only if this doc is primarily ABOUT
        the query topic, not just mentioning it.
        """
        doc_terms = doc_vectors[doc_id]
        
        # How much of this doc's vocabulary overlaps with query?
        query_overlap = sum(
            doc_terms.get(t, 0) for t in query_stems
        )
        
        # Docs primarily about the topic have high overlap
        # Docs merely mentioning it have low overlap
        return query_overlap > 0.15  # tune this threshold

    def expand(self, query_text, rel_doc_ids, non_rel_doc_ids, top_k=5):
        raw_tokens = [t for t in query_text.lower().split() if t not in self.stop_words]
        query_stems = {self.stemmer.stem(t) for t in raw_tokens}
        q0 = self._get_query_vector(query_text)
        
        # 1. Optimize Document Vector Generation (O(V))
        target_docs = set(rel_doc_ids) | set(non_rel_doc_ids)
        doc_vectors = {doc_id: defaultdict(float) for doc_id in target_docs}
        
        for term, postings in self.indexer.index.items():
            intersection = target_docs.intersection(postings.keys())
            if intersection:
                idf = self._get_idf(term)
                if idf == 0: continue
                for doc_id in intersection:
                    tf = postings[doc_id]
                    doc_vectors[doc_id][term] = (1 + math.log10(tf)) * idf
                    
        for doc_id in target_docs:
            doc_vectors[doc_id] = self._normalize(doc_vectors[doc_id])

        term_rel_doc_counts = defaultdict(int)
        term_non_rel_doc_counts = defaultdict(int)
        
        dr_centroid = defaultdict(float)
        if rel_doc_ids:
            trusted_rel_ids = [
                doc_id for doc_id in rel_doc_ids 
                if self._is_trustworthy_rel_doc(doc_id, query_stems, doc_vectors)
            ]
            
            if not trusted_rel_ids:
                trusted_rel_ids = rel_doc_ids
                
            for doc_id in trusted_rel_ids:
                vec = doc_vectors[doc_id]
                for term, val in vec.items():
                    dr_centroid[term] += val / len(trusted_rel_ids)
                    term_rel_doc_counts[term] += 1
                    
        dnr_centroid = defaultdict(float)
        if non_rel_doc_ids:
            for doc_id in non_rel_doc_ids:
                vec = doc_vectors[doc_id]
                for term, val in vec.items():
                    dnr_centroid[term] += val / len(non_rel_doc_ids)
                    term_non_rel_doc_counts[term] += 1

        qm = defaultdict(float)
        all_terms = set(q0.keys()) | set(dr_centroid.keys()) | set(dnr_centroid.keys())
        
        stemmed_tokens = [self.stemmer.stem(t) for t in raw_tokens]
        for term in all_terms:
            val = (self.alpha * q0.get(term, 0)) + \
                  (self.beta * dr_centroid.get(term, 0)) - \
                  (self.gamma * dnr_centroid.get(term, 0))
            
            if val > 0:
                # 4. Contrastive Relevance (Negative Evidence)
                rel_freq = term_rel_doc_counts.get(term, 0)
                non_rel_freq = term_non_rel_doc_counts.get(term, 0)
                contrast_score = (rel_freq + 1) / (non_rel_freq + 1)
                
                # Dynamic Query Bias & IDF Weighting
                query_bias = self._get_query_bias(term, stemmed_tokens, dr_centroid)
                idf_weight = 1 + self._get_idf(term)
                
                qm[term] = val * contrast_score * query_bias * idf_weight

        all_scores = list(qm.values())
        mean_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        seen_stems = set(query_stems)
        sorted_candidates = sorted(qm.items(), key=lambda x: x[1], reverse=True)
        
        expansion_candidates = []
        for term, score in sorted_candidates:
            
            # 3. Dynamic Stopword/Length filter instead of hardcoded lengths
            if term in self.stop_words or len(term) <= 2: continue
            
            if score <= (mean_score * 1.5): continue
            if term_rel_doc_counts.get(term, 0) < 2: continue
            
            # Deduplication
            stem = self.stemmer.stem(term)
            if stem in seen_stems: continue
            seen_stems.add(stem)
            
            expansion_candidates.append((term, score))
            
            if len(expansion_candidates) >= top_k:
                break

        return expansion_candidates
