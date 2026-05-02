import os
import sys
import json
import re
from collections import defaultdict, Counter
import math

# Add parent directory to path to import Nikita's indexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexing_relevance.indexer import PredatorIndexer
from query_expansion.rocchio import RocchioExpander

def generate_visual_report(query_text):
    print(f"Generating Precision Report for: '{query_text}'...")
    
    indexer = PredatorIndexer("data/pages")
    indexer.load_from_disk()
    indexer.load_mapping("data/url_mapping.jsonl")
    indexer.load_link_scores("link_analysis_scores.pkl")
    rocchio = RocchioExpander(indexer)
    
    # Section 1: Local Document Set
    print("\n1) Local document set (URL : score)")
    results = indexer.fused_search(query_text, top_n=50)
    doc_ids = []
    seen_urls = set()
    
    query_stems = {
        rocchio.stemmer.stem(t) 
        for t in query_text.lower().split() 
        if t not in rocchio.stop_words
    }
    raw_tokens = [t for t in query_text.lower().split() if t not in rocchio.stop_words]
    search_terms = set(raw_tokens) | query_stems
    
    non_rel_docs = []
    
    for i, res in enumerate(results):
        url_normalized = res['url'].lower()
        url_base = url_normalized.split('#')[0]
        if url_base in seen_urls:
            continue
        seen_urls.add(url_base)
        
        doc_id = None
        for d_id, url in indexer.url_map.items():
            if url == res['url']:
                doc_id = d_id
                break
                
        if not doc_id and res['url'].startswith('page_'):
            doc_id = res['url']
            
        if not doc_id:
            continue
            
        if i < 15 and len(doc_ids) < 5:
            overlap = sum(1 for t in search_terms if doc_id in indexer.index.get(t, {}))
            if overlap >= min(2, len(query_stems)):
                print(f"- {res['url']} ||| {res['score']:.4f}")
                doc_ids.append(doc_id)
        elif len(non_rel_docs) < 10 and i >= 40:
            non_rel_docs.append(doc_id)
            
    if not doc_ids:
        print("\nNo documents passed the overlap filter. Aborting expansion.")
        sys.exit(0)
    
    # Section 2: Local Vocabulary & stems
    print("\n2) Local vocabulary & stems")
    local_vocab = set()
    for d_id in doc_ids:
        for term, postings in indexer.index.items():
            if d_id in postings:
                if term not in indexer.stopwords and len(term) > 4:
                    local_vocab.add(term)
    
    sorted_vocab = sorted(list(local_vocab))
    print(";".join(sorted_vocab[:200]) + "...")

    # Section 3: Expansion info (term | Rocchio score)
    print("\n3) Expansion info (term | score)")
    # Use the real Rocchio expander with its new precision filters
    expanded_list = rocchio.expand(query_text, doc_ids, non_rel_docs, top_k=5)
    
    for term, score in expanded_list:
        print(f"- {term} | {score:.4f}")
        
    # Section 4: Expanded query
    print("\n4) Expanded query")
    expanded_terms = [t[0] for t in expanded_list]
    print(f"{query_text} {' '.join(expanded_terms)}")

if __name__ == "__main__":
    generate_visual_report("Bengal Tiger habitat loss")
