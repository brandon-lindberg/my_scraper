# main.py

import json
import os
from scraper import crawl_website

def main():
    # Load the URLs from the JSON file
    urls_file = 'urls.json'
    if not os.path.exists(urls_file):
        print(f"Error: {urls_file} not found.")
        return

    with open(urls_file, 'r', encoding='utf-8') as f:
        sites = json.load(f)  # Expecting a list of { "id": "...", "url": "..." }

    all_results = []

    for site_info in sites:
        site_id = site_info.get("id")
        url = site_info.get("url")
        if not site_id or not url:
            print(f"Skipping invalid site entry: {site_info}")
            continue

        print(f"[*] Starting crawl for site ID {site_id} - {url}")
        site_pages_data = crawl_website(site_id, url, max_pages=10)
        all_results.extend(site_pages_data)

    # Write combined results to a JSON file
    output_file = 'scraped_output.json'
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(all_results, out, ensure_ascii=False, indent=2)

    print(f"Done! Scraped data written to {output_file}")

if __name__ == "__main__":
    main()
