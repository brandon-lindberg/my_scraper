# scraper.py

import requests
import datetime
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_page(url):
    """
    Fetch the HTML content from a given URL using requests.
    Returns the raw HTML string if successful, otherwise None.
    """
    # Mimic a common browser user-agent to avoid 403 or blocking
    custom_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.114 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, timeout=10, headers=custom_headers)
        response.raise_for_status()  # raise an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_page(html, url):
    """
    Parse the HTML using BeautifulSoup and return a dictionary with:
        {
          "url": ...,
          "title": ...,
          "headers": {
              "h1": ...,
              "h2": [...],
              ...
          },
          "data": ...,
          "links": [...],
          "scrapedAt": ...
        }
    """
    soup = BeautifulSoup(html, 'lxml')

    # Extract <title>
    title = soup.title.string.strip() if soup.title else None

    # Extract headers
    headers = {}
    h1 = soup.find_all('h1')
    h2 = soup.find_all('h2')
    h3 = soup.find_all('h3')

    if h1:
        # If multiple h1s exist, store them all, or just the first. Your choice:
        headers['h1'] = [tag.get_text(strip=True) for tag in h1]
    if h2:
        headers['h2'] = [tag.get_text(strip=True) for tag in h2]
    if h3:
        headers['h3'] = [tag.get_text(strip=True) for tag in h3]

    # Remove scripts and styles to get main text
    for script_style in soup(['script', 'style']):
        script_style.extract()
    page_text = soup.get_text(separator=' ', strip=True)

    # Extract absolute links
    links = []
    for a_tag in soup.find_all('a', href=True):
        absolute_link = urljoin(url, a_tag['href'])
        # You can filter out mailto:, javascript:, #, etc. if desired
        if absolute_link.startswith('http'):
            links.append(absolute_link)

    scraped_data = {
        "url": url,
        "title": title,
        "headers": headers,
        "data": page_text,
        "links": links,
        "scrapedAt": datetime.datetime.utcnow().isoformat() + "Z"
    }

    return scraped_data

def crawl_website(site_id, base_url, max_pages=225):
    """
    Crawl the website starting from base_url in a BFS manner,
    scraping all pages up to max_pages.
    Returns a list of dictionaries, one per page.
    """
    to_visit = [base_url]
    visited = set()
    results = []

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)

        # Skip if we've already visited
        if current_url in visited:
            continue

        visited.add(current_url)

        # (Optional) Sleep to reduce load or avoid rate-limiting
        time.sleep(1)

        # Fetch and parse the current page
        html = fetch_page(current_url)
        if not html:
            continue  # Skip if we failed to retrieve the page

        page_data = parse_page(html, current_url)
        # Add a custom "id" that merges site_id and a running count
        page_data['id'] = f"{site_id}-{len(visited)}"
        results.append(page_data)

        # Enqueue all newly found links that haven't been visited yet
        # and that belong to the same domain if you want to restrict the crawl
        for link in page_data['links']:
            # Example: Only crawl links that start with the base_url's domain
            if link.startswith(base_url) and link not in visited:
                to_visit.append(link)

    return results
