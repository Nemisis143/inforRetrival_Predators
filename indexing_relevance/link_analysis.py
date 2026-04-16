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
                # 1. Start with the damping factor (the "random jump")
                rank = (1.0 - damping) / N
                
                # 2. Add the sink distribution (dangling nodes)
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

    # Quick Top 5 PageRank check
    top_pr = sorted(analyzer.pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nTop 5 Pages by PageRank:")
    for url, score in top_pr:
        print(f"{score:.6f} - {url}")