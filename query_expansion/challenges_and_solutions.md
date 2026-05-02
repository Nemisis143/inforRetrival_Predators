# Technical Challenges and Solutions: Predator Search Engine

This document outlines the key technical hurdles encountered during the development of the Predator Search Engine and the strategies implemented to overcome them.

## 1. Scalability and Memory Management
**Challenge:** Indexing and searching a corpus of over 100,000 web pages caused significant memory overhead and slow loading times.
**Solution:**
*   Implemented **Pickle-based serialization** for the inverted index, reducing load times from minutes to ~35 seconds.
*   Utilized **Forward Indexing** only for highly relevant terms during clustering to keep the memory footprint within manageable limits.
*   Used `defaultdict` and list comprehensions to optimize frequency calculations.

## 2. Concept Drift in Query Expansion
**Challenge:** The Rocchio algorithm and term-clustering occasionally pulled in irrelevant terms (e.g., prey species like "buffalo" or habitat terms like "grasslands") instead of predator-focused terms.
**Solution:**
*   **IDF-Weighted Co-occurrence:** In the clustering engine, we weighted co-occurring terms by their Inverse Document Frequency. This penalized common words and prioritized specialized predatory vocabulary.
*   **Beta/Gamma Tuning:** Fine-tuned the Rocchio parameters (β=0.75, γ=0.15) to emphasize the centroid of relevant documents while minimizing the impact of non-relevant noise.

## 3. Link Analysis Fusion
**Challenge:** Standard TF-IDF ranking often prioritized "keyword-stuffed" pages over authoritative sources.
**Solution:**
*   **Fused Search Ranking:** Developed a custom scoring formula: `Score = (TF-IDF + (PageRank * 1000)) * CoordinationFactor * URLWeight`.
*   This ensured that pages with high link authority (PageRank) were boosted, and "deep" content pages were prioritized over broad homepages.

## 4. Normalizing Clustering Similarities
**Challenge:** Raw co-occurrence counts in Association clusters favored terms that were globally frequent, regardless of their semantic relationship to the query.
**Solution:**
*   Implemented **Metric and Scalar similarity** measures. These algorithms normalize the co-occurrence by the norms of the individual terms (Jaccard-like for Metric, Cosine-like for Scalar), ensuring that the expansion terms are truly semantically linked to the query term.

## 5. Ad-hoc Query Latency
**Challenge:** Re-running the search script for every new user query during a demo was impossible due to the 35-second index loading time.
**Solution:**
*   **Persistent Search API:** Developed a Flask-based Web API and an Interactive CLI tool that loads the index into memory **once**.
*   This enables **sub-second response times** for ad-hoc queries, making the search engine feel "live" and responsive during presentations.

## 6. Corpus Diversity
**Challenge:** Ensuring the 100k-page crawl covered both specific predatory behaviors and broad ecological contexts.
**Solution:**
*   **Hybrid Seed Strategy:** Used a mix of 20 highly specific "Niche" queries (e.g., "African Lion cooperative hunting") and 50 "Broad" queries to guide the crawler into different segments of the web.
