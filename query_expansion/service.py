import os
import sys
from .rocchio import RocchioExpander
from .expansion_clusters import ClusterExpander
import math
import nltk
from nltk.corpus import stopwords

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class ExpansionService:
    def __init__(self, indexer):
        """
        Main entry point for Query Expansion in the Predator Search Engine.
        To be used by the GUI / Frontend team.
        """
        self.indexer = indexer
        self.rocchio = RocchioExpander(indexer)
        self.clusters = ClusterExpander(indexer)
        self.url_to_doc_id = {url: doc_id for doc_id, url in self.indexer.url_map.items()}

    def expand_query(self, query_text, method='rocchio', top_k=3):
        """
        Returns an expanded query string based on the chosen method.
        """
        if method == 'rocchio':
            initial_results = self.indexer.fused_search(query_text, top_n=50)
            
            # Get query stems for overlap checking
            query_stems = {
                self.rocchio.stemmer.stem(t) 
                for t in query_text.lower().split() 
                if t not in self.rocchio.stop_words
            }
            raw_tokens = [t for t in query_text.lower().split() if t not in self.rocchio.stop_words]
            # Use both raw and stemmed tokens to ensure we catch unstemmed index hits quickly without O(V) scanning
            search_terms = set(raw_tokens) | query_stems
            
            rel_docs = []
            non_rel_docs = []
            seen_urls = set()  # Fix 1: deduplicate URLs
            
            for i, res in enumerate(initial_results):
                # Fix 2: normalize URL case to catch duplicates
                url_normalized = res['url'].lower()
                # Strip anchor tags to prevent duplicates like page/ and page/#section
                url_base = url_normalized.split('#')[0]
                if url_base in seen_urls:
                    continue
                seen_urls.add(url_base)
                
                doc_id = self.url_to_doc_id.get(res['url'])
                if not doc_id and res['url'].startswith('page_'):
                    doc_id = res['url']
                    
                if not doc_id:
                    continue
                    
                if i < 15 and len(rel_docs) < 3:  # Fix 3: look at wider pool
                    # Fix 4: only trust as relevant if overlaps with query
                    overlap = sum(1 for t in search_terms if doc_id in self.indexer.index.get(t, {}))
                    
                    if overlap >= min(2, len(query_stems)):
                        rel_docs.append(doc_id)
                        
                elif i >= 40:
                    non_rel_docs.append(doc_id)
            
            # If still empty, better to expand nothing than expand wrong
            if not rel_docs:
                return query_text
            
            expanded_terms = self.rocchio.expand(query_text, rel_docs, non_rel_docs)
            new_terms = [t[0] for t in expanded_terms]
            return f"{query_text} {' '.join(new_terms)}"

        elif method in ['association', 'metric', 'scalar']:
            # 1. Use the standard NLTK library to remove grammar (no hardcoded lists!)
            stop_words = set(stopwords.words('english'))
            query_words = [w.lower() for w in query_text.split() if w.lower() not in stop_words]
            
            if not query_words:
                return query_text

            aggregated_scores = {}
            num_docs = len(self.indexer.url_map) # Get total docs for IDF math
            
            # 2. Get expansions for ALL valid words in the query
            for word in query_words:
                if method == 'association':
                    terms = self.clusters.get_association_expansion(word, top_k=top_k + 5)
                elif method == 'metric':
                    terms = self.clusters.get_metric_expansion(word, top_k=top_k + 5)
                else:
                    terms = self.clusters.get_scalar_expansion(word, top_k=top_k + 5)
                
                # 3. Apply IDF to the cluster results!
                for term, cluster_score in terms:
                    # Skip if we already typed it, or if it's a grammar stopword
                    if term in query_words or term in stop_words or len(term) <= 3: 
                        continue
                        
                    # Calculate IDF (How rare/important is this word globally?)
                    df = len(self.indexer.index.get(term, {}))
                    if df > 0:
                        idf = math.log10(num_docs / df)
                    else:
                        idf = 0.0
                        
                    # Multiply the cluster's similarity score by the global IDF
                    # This protects scientific terms and kills common noise!
                    final_score = cluster_score * idf
                    
                    aggregated_scores[term] = aggregated_scores.get(term, 0) + final_score
            
            # 4. Sort by the highest aggregated IDF-weighted score
            best_terms = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            new_terms = [t[0] for t in best_terms]
            
            return f"{query_text} {' '.join(new_terms)}"
            
        return query_text

if __name__ == "__main__":
    # Example usage for integration testing
    pass
