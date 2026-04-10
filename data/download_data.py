import os
import csv
import time, argparse
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
from multiprocessing import Pool, Manager, Lock

def safe_filename(url):
    return hashlib.md5(url.encode()).hexdigest() + ".html"


def save_html(content, url):
    os.makedirs('pages', exist_ok=True)
    filename = os.path.join('pages', safe_filename(url))

    if os.path.exists(filename):
        return filename

    with open(filename, "w", encoding='utf-8') as f:
        f.write(content)
    return filename


def crawl_url(args):
    url, seed_domain, q, dataset, dataset_lock, visited, visited_lock, max_pages = args

    with visited_lock:
        if len(visited) >= max_pages or url in visited:
            return
        visited[url] = True

    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else ""
        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]

        html_file = save_html(response.text, url)

        with dataset_lock:
            dataset.append({
                'url': url,
                'title': title,
                'num_pages': len(links),
                'html_file': html_file
            })

        for link in links:
            parsed = urlparse(link)
            link_domain = tldextract.extract(parsed.netloc).domain

            if seed_domain == link_domain:
                q.put(link)

    except Exception as e:
        print(f"❌ Error crawling {url}: {e}")


def crawl(seed_url, max_pages=100, num_processes=4):
    manager = Manager()
    q = manager.Queue()
    dataset = manager.list()
    visited = manager.dict()
    dataset_lock = manager.Lock()
    visited_lock = manager.Lock()

    seed_domain = tldextract.extract(seed_url).domain
    q.put(seed_url)

    with Pool(processes=num_processes) as pool:
        tasks = []

        while True:
            while not q.empty() and len(visited) < max_pages:
                url = q.get()
                if url in visited:
                    continue
                args = (url, seed_domain, q, dataset, dataset_lock, visited, visited_lock, max_pages)
                task = pool.apply_async(crawl_url, (args,))
                tasks.append(task)

            time.sleep(0.5)

            # ✅ Exit if enough pages visited or queue + active tasks done
            if len(visited) >= max_pages or (q.empty() and all(task.ready() for task in tasks)):
                break


        pool.close()
        pool.join()

    # Save to CSV
    with open("crawled_data.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title', 'num_pages', 'html_file'])
        writer.writeheader()
        writer.writerows(list(dataset))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Crawl the website and download page data")

    parser.add_argument("--base_url", type=str, required=True, help="URL address")
    parser.add_argument("--max_pages", type=int, default=10, help="Maximum number of pages to process")
    parser.add_argument("--num_processes", type=int, help="Number of processors to utilize")

    args = parser.parse_args()

    # Fix: Use default if not passed
    num_processes = args.num_processes or os.cpu_count()

    crawl(args.base_url, args.max_pages, num_processes)
