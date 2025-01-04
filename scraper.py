# scraper.py

import requests
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_page(url):
    """
    Fetches the HTML content from a given URL using requests.
    Returns the raw HTML string if successful, otherwise None.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raise an HTTPError if the response was unsuccessful
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_page(html, url):
    """
    Parses the HTML using BeautifulSoup, and returns a dictionary
    matching the desired structure:
        {
          "id": ...,
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
    # For example, we collect all h1, h2, etc.
    h1 = soup.find_all('h1')
    h2 = soup.find_all('h2')
    h3 = soup.find_all('h3')
    if h1:
        # If there are multiple h1s, store the first or store them all - your choice
        headers['h1'] = h1[0].get_text(strip=True) if len(h1) == 1 else [tag.get_text(strip=True) for tag in h1]
    if h2:
        headers['h2'] = [tag.get_text(strip=True) for tag in h2]
    if h3:
        headers['h3'] = [tag.get_text(strip=True) for tag in h3]

    # Extract raw text from the page (excluding scripts/styles)
    # This can be as refined or raw as you want
    for script_style in soup(['script', 'style']):
        script_style.extract()
    page_text = soup.get_text(separator=' ', strip=True)

    # Extract all links (absolute URLs)
    links = []
    for a_tag in soup.find_all('a', href=True):
        absolute_link = urljoin(url, a_tag['href'])
        # optionally filter out mailto: or # or javascript: links
        if absolute_link.startswith('http'):
            links.append(absolute_link)

    # Build your dictionary
    scraped_data = {
        # "id": will be assigned later (either from our JSON file or a separate incremental)
        "url": url,
        "title": title,
        "headers": headers,
        "data": page_text,
        "links": links,
        "scrapedAt": datetime.datetime.utcnow().isoformat() + "Z"
    }

    return scraped_data

def crawl_website(site_id, base_url, max_pages=5):
    """
    A simple BFS/DFS to crawl a site up to `max_pages` links deep.
    Returns a list of dictionaries, one per page.
    """
    to_visit = [base_url]
    visited = set()
    results = []

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        visited.add(current_url)
        html = fetch_page(current_url)
        if not html:
            continue

        page_data = parse_page(html, current_url)
        # Add the site_id
        page_data['id'] = f"{site_id}-{len(visited)}"
        results.append(page_data)

        # Add new links to the queue
        for link in page_data["links"]:
            if link not in visited and link.startswith(base_url):
                to_visit.append(link)

    return results
