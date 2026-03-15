#pdf_scraper.py
import os
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SEED_URLS = [
    "https://www.daiict.ac.in/examination-department",
    "https://www.daiict.ac.in/ai-ml-and-data-science",
    "https://www.daiict.ac.in/sponsored-projects",
    "https://www.daiict.ac.in/dau-student-research-excellence-award",
    "https://www.daiict.ac.in/faculty-research-publication-incentive"
]
OUTPUT_DIR = "./data/raw"


def scrape_pdfs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )

    for url in SEED_URLS:
        print(f"\n[*] Fetching page: {url}")
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = soup.find_all("a", href=lambda h: h and h.lower().endswith(".pdf"))

        print(f"[*] Found {len(pdf_links)} PDF link(s) on {url}")

        for link in pdf_links:
            pdf_url = urljoin(url, link["href"])
            filename = os.path.basename(pdf_url)

            filepath = os.path.join(OUTPUT_DIR, filename)

            try:
                print(f"[*] Downloading: {filename}")
                pdf_response = session.get(pdf_url, stream=True, timeout=60)
                pdf_response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"[+] Successfully saved: {filepath}")
            except requests.RequestException as e:
                print(f"[!] Failed to download {pdf_url}: {e}")

            time.sleep(1)


if __name__ == "__main__":
    scrape_pdfs()
