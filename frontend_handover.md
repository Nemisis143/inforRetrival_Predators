# Frontend Integration Guide for Khushi

To display the Predator Search Engine results in the UI, please follow these instructions.

## 1. Connecting to the Backend
The backend is a Flask API. To receive results, make a `GET` request to:
`http://localhost:5000/search?q=USER_QUERY`

## 2. Response Structure
The API returns a JSON object with the following keys:

### Expanded Queries (To be displayed above results)
*   `expanded_query_rocchio`: The query terms added by the Rocchio algorithm.
*   `expanded_query_assoc`: Terms from Association Clustering.
*   `expanded_query_metric`: Terms from Metric Clustering.
*   `expanded_query_scalar`: Terms from Scalar Clustering.

### Result Sets (For the comparison UI)
The `results` object contains different lists of documents based on the toggles selected in the UI:
*   `results.base_tfidf`: Standard search (No PageRank, No Expansion).
*   `results.with_pagerank`: Search with Link Analysis active.
*   `results.with_rocchio`: Search using the Rocchio Expanded query.
*   `results.cluster_association`: Search using Association Clustering.
*   `results.cluster_metric`: Search using Metric Clustering.
*   `results.cluster_scalar`: Search using Scalar Clustering.

### Document Format
Each document in the lists above has:
*   `title`: The title of the page (extracted from the first line).
*   `url`: The source URL.
*   `snippet`: A 200-character preview of the content.
*   `score`: The relevance score (for sorting or debugging).

## 3. Example Usage (JavaScript)
```javascript
async function getResults(query) {
    const response = await fetch(`http://localhost:5000/search?q=${query}`);
    const data = await response.json();
    
    // Display the expanded query
    document.getElementById('expansion-text').innerText = data.expanded_query_rocchio;
    
    // Display the results list
    renderResults(data.results.with_pagerank); 
}
```

## 4. Comparison View
For the **Google/Bing comparison**, you can find pre-crawled results in **`query_expansion/competitor_results.json`** to display side-by-side with our internal results.
