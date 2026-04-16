import json
import os
import pickle
from collections import defaultdict

class PredatorLinkAnalyzer:
    def __init__(self, graph_path):
        self.graph_path = graph_path
        self.out_links = defaultdict(list)
        self.in_links = defaultdict(list)
        self.nodes = set()
        self.pagerank_scores = {}
        self.hub_scores = {}
        self.authority_scores = {}

    def build_graph(self):
        print("Building graph and In-Link map...")
        with open(self.graph_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    src, dst = data['src'], data['dst']
                    
                    self.out_links[src].append(dst)
                    self.in_links[dst].append(src)
                    self.nodes.add(src)
                    self.nodes.add(dst)
                except json.JSONDecodeError:
                    continue
        print(f"Graph built: {len(self.nodes)} nodes.")

    def calculate_pagerank(self, damping=0.85, iterations=20):
        print(f"Calculating PageRank ({iterations} iterations)...")
        N = len(self.nodes)
        if N == 0: return
        
        # Initial score 1/N
        scores = {node: 1.0 / N for node in self.nodes}
        
        for i in range(iterations):
            new_scores = {}
            sink_sum = sum(scores[node] for node in self.nodes if not self.out_links[node])
            
            for node in self.nodes:
                # 1. Start with the damping factor 
                rank = (1.0 - damping) / N
                
                # 2. Add the sink distribution 
                rank += damping * (sink_sum / N)
                
                # 3. Add scores from pages that link TO this node
                for incoming in self.in_links[node]:
                    out_count = len(self.out_links[incoming])
                    rank += damping * (scores[incoming] / out_count)
                
                new_scores[node] = rank
            
            scores = new_scores
            print(f"Iteration {i+1} complete.")
        
        self.pagerank_scores = scores

    def calculate_hits(self, iterations=20):
        """Calculates Hubs and Authorities scores"""
        print("Calculating HITS...")
        # Initialize scores to 1.0
        hubs = {node: 1.0 for node in self.nodes}
        auths = {node: 1.0 for node in self.nodes}

        for i in range(iterations):
            # Update Authorities based on Hubs
            new_auths = {}
            norm_auth = 0
            for node in self.nodes:
                score = sum(hubs[incoming] for incoming in self.in_links[node])
                new_auths[node] = score
                norm_auth += score**2
            
            # Normalize Auth
            norm_auth = norm_auth**0.5
            for node in self.nodes: auths[node] = new_auths[node] / (norm_auth or 1)

            # Update Hubs based on Authorities
            new_hubs = {}
            norm_hub = 0
            for node in self.nodes:
                score = sum(auths[outgoing] for outgoing in self.out_links[node])
                new_hubs[node] = score
                norm_hub += score**2
            
            # Normalize Hubs
            norm_hub = norm_hub**0.5
            for node in self.nodes: hubs[node] = new_hubs[node] / (norm_hub or 1)

        self.hub_scores = hubs
        self.authority_scores = auths
        print("HITS calculation complete.")

    def save_all_scores(self):
        data = {
            'pagerank': self.pagerank_scores,
            'hubs': self.hub_scores,
            'authorities': self.authority_scores
        }
        with open('link_analysis_scores.pkl', 'wb') as f:
            pickle.dump(data, f)
        print("All scores saved to link_analysis_scores.pkl")

if __name__ == "__main__":
    GRAPH_PATH = os.path.join('data', 'web_graph.jsonl')
    
    analyzer = PredatorLinkAnalyzer(GRAPH_PATH)
    analyzer.build_graph()
    analyzer.calculate_pagerank()
    analyzer.calculate_hits()
    analyzer.save_all_scores()

    # Print summary statistics
   
    print("--- GRAPH STATISTICS ---")
    
    print(f"Total Nodes: {len(analyzer.nodes)}")
    
    total_edges = sum(len(dests) for dests in analyzer.out_links.values())
    print(f"Total Links (Edges): {total_edges}")
    
    if analyzer.nodes:
        max_in_node = max(analyzer.nodes, key=lambda n: len(analyzer.in_links[n]))
        print(f"Largest In-degree: {len(analyzer.in_links[max_in_node])} links (Node: {max_in_node})")
        
        max_out_node = max(analyzer.nodes, key=lambda n: len(analyzer.out_links[n]))
        print(f"Largest Out-degree: {len(analyzer.out_links[max_out_node])} links (Node: {max_out_node})")

    # Print top PageRank scores
    print("\n--- Top 5 Pages by PageRank ---")
    top_pr = sorted(analyzer.pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    for url, score in top_pr:
        print(f"{score:.6f} - {url}")

    # Print top HITS scores
    print("\n--- Top 5 Authorities (HITS) ---")
    top_auths = sorted(analyzer.authority_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    for url, score in top_auths: 
        print(f"{score:.6f} - {url}")

    print("\n--- Top 5 Hubs (HITS) ---")
    top_hubs = sorted(analyzer.hub_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    for url, score in top_hubs: 
        print(f"{score:.6f} - {url}")