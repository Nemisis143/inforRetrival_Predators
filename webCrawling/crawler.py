import asyncio
import aiohttp
import aiofiles
import json
import os
import ssl
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

MAX_PAGES = 100000
CONCURRENT_REQUESTS = 80 
TIMEOUT_SECONDS = 5

BASE_DIR = os.path.expanduser("/Users/jammulasandeep/Downloads/Predators") #Edit to local path, if you want to run the crawler.
PAGES_DIR = os.path.join(BASE_DIR, "pages")
GRAPH_FILE = os.path.join(BASE_DIR, "web_graph.jsonl")
CHECKPOINT_FILE = os.path.join(BASE_DIR, "checkpoint.json")

for d in [BASE_DIR, PAGES_DIR]:
    if not os.path.exists(d): os.makedirs(d)

class PredatorCrawler:
    def __init__(self, seeds):
        self.visited = set()
        self.frontier_list = list(seeds)
        self.frontier = asyncio.Queue()
        self.count = 0
        self.graph_lock = asyncio.Lock()
        
        #To resume the crawler in case of crash, exisiting checkpoint file is used.
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                self.visited = set(data.get('visited', []))
                self.frontier_list = data.get('frontier', seeds)
                self.count = len(self.visited)
            print(f"Resuming from checkpoint: {self.count} pages.")

        for url in self.frontier_list:
            self.frontier.put_nowait(url)

    #Ascychronous implementation of scraping due to hardware limitations. If your hardware can handle it, multithreading is preferred.
    async def save_checkpoint(self):
        current_frontier = []
        temp_queue = []
        while not self.frontier.empty():
            item = self.frontier.get_nowait()
            current_frontier.append(item)
            temp_queue.append(item)
        
        for item in temp_queue:
            self.frontier.put_nowait(item)

        async with aiofiles.open(CHECKPOINT_FILE, mode='w') as f:
            await f.write(json.dumps({
                'visited': list(self.visited),
                'frontier': current_frontier[:50000] # Cap size for speed
            }))

    async def fetch(self, session, url):
        if url in self.visited or self.count >= MAX_PAGES:
            return
        
        self.visited.add(url)

        try:
            async with session.get(url, timeout=TIMEOUT_SECONDS, ssl=False) as response:
                if response.status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml' if 'lxml' else 'html.parser')
                    text = soup.get_text()
                    
                    self.count += 1
                    page_path = os.path.join(PAGES_DIR, f"page_{self.count}.txt")
                    async with aiofiles.open(page_path, mode='w', encoding='utf-8') as f:
                        await f.write(text)
                    
                    links = []
                    for a in soup.find_all('a', href=True):
                        link = urljoin(url, a['href'])
                        if urlparse(link).netloc:
                            links.append(link)
                            if link not in self.visited and self.frontier.qsize() < 200000:
                                self.frontier.put_nowait(link)
                    
                    async with self.graph_lock:
                        async with aiofiles.open(GRAPH_FILE, mode='a') as g:
                            for dst in links:
                                await g.write(json.dumps({"src": url, "dst": dst}) + "\n")
                    
                    # Save checkpoint every 100 pages
                    if self.count % 100 == 0:
                        await self.save_checkpoint()
                        print(f"Saved Checkpoint: {self.count}/{MAX_PAGES} | Queue: {self.frontier.qsize()}")
        except:
            pass

    async def worker(self, session):
        while self.count < MAX_PAGES:
            try:
                url = await asyncio.wait_for(self.frontier.get(), timeout=10)
                await self.fetch(session, url)
                self.frontier.task_done()
            except asyncio.TimeoutError:
                if self.count >= MAX_PAGES: break
                continue

    async def run(self):
        connector = aiohttp.TCPConnector(limit_per_host=10, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            session.headers.update({'User-Agent': 'UTD-CS6322-Group5-PredatorBot/1.0'})
            workers = [asyncio.create_task(self.worker(session)) for _ in range(CONCURRENT_REQUESTS)]
            await asyncio.gather(*workers)

#You can update with your starting seeds and crawl a different set of websites.
SEEDS = [
    "https://en.wikipedia.org/wiki/Predation",
    "https://www.britannica.com/animal/predator",
    "https://www.nationalgeographic.com/animals",
    "https://www.worldwildlife.org/",
    "https://animaldiversity.org/",
    "https://www.nature.com/subjects/predation"
]

if __name__ == "__main__":
    crawler = PredatorCrawler(SEEDS)
    try:
        asyncio.run(crawler.run())
    except KeyboardInterrupt:
        print("\nSaving final checkpoint...")
        # Note: In a real crash, a manual final save here is good practice