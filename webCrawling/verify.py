import os
import json

#Add your local path where you stored crawling results.
BASE_DIR = os.path.expanduser("/Users/jammulasandeep/Downloads/Predators")
PAGES_DIR = os.path.join(BASE_DIR, "pages")
GRAPH_FILE = os.path.join(BASE_DIR, "web_graph.jsonl")

def verify_crawl():
    print("--- Starting Crawl Verification ---")
    
    #Page Count Check
    if not os.path.exists(PAGES_DIR):
        print("Error: Pages directory not found.")
        return
    
    files = [f for f in os.listdir(PAGES_DIR) if f.endswith(".txt")]
    file_count = len(files)
    print(f"Total Pages Found: {file_count}")
    
    if file_count < 100000:
        print(f"Warning: You have {file_count} pages, which is less than the 100,000 required.")
    
    #Empty and Junk Files Check
    empty_files = 0
    small_files = 0 # Files under 100 bytes are likely junk/errors
    for f_name in files:
        f_path = os.path.join(PAGES_DIR, f_name)
        size = os.path.getsize(f_path)
        if size == 0:
            empty_files += 1
        elif size < 100:
            small_files += 1
            
    print(f"Empty Files: {empty_files}")
    print(f"Small/Junk Files (<100 bytes): {small_files}")
    
    #Web Graph Edge check
    print("\n--- Verifying Web Graph ---")
    if not os.path.exists(GRAPH_FILE):
        print("Error: web_graph.jsonl not found.")
        return

    edge_count = 0
    corrupt_lines = 0
    unique_sources = set()
    
    with open(GRAPH_FILE, 'r') as g:
        for i, line in enumerate(g):
            try:
                data = json.loads(line)
                if 'src' in data and 'dst' in data:
                    edge_count += 1
                    unique_sources.add(data['src'])
                else:
                    corrupt_lines += 1
            except json.JSONDecodeError:
                corrupt_lines += 1

    print(f"Total Graph Edges: {edge_count}")
    print(f"Unique Source URLs in Graph: {len(unique_sources)}")
    print(f"Corrupt/Invalid Lines: {corrupt_lines}")
    
    if edge_count == 0:
        print("Error: The web graph is empty. Nikita cannot run PageRanking.")
    elif len(unique_sources) < (file_count * 0.5):
        print("Warning: Low source coverage in graph. Link analysis might be weak.")

if __name__ == "__main__":
    verify_crawl()