import requests
from bs4 import BeautifulSoup
import json
import time

def get_japanese_locations():
    """Return a list of Japanese locations to scrape"""
    return [
        {"name": "Tokyo", "url": "https://www.international-schools-database.com/in/tokyo"},
        {"name": "Kyoto-Osaka-Kobe", "url": "https://www.international-schools-database.com/in/kyoto-osaka-kobe"},
        {"name": "Nagoya", "url": "https://www.international-schools-database.com/in/nagoya"},
        {"name": "Tsukuba", "url": "https://www.international-schools-database.com/in/tsukuba"},
        {"name": "Nagano", "url": "https://www.international-schools-database.com/in/nagano"},
        {"name": "Sapporo", "url": "https://www.international-schools-database.com/in/sapporo-hokkaido"},
        {"name": "Okinawa", "url": "https://www.international-schools-database.com/in/okinawa"},
        {"name": "Sendai", "url": "https://www.international-schools-database.com/in/sendai"},
        {"name": "Hiroshima", "url": "https://www.international-schools-database.com/in/hiroshima"},
        {"name": "Fukuoka", "url": "https://www.international-schools-database.com/in/fukuoka"},
        {"name": "Appi Kogen", "url": "https://www.international-schools-database.com/in/appi-kogen"},
        {"name": "Kofu", "url": "https://www.international-schools-database.com/in/kofu"}
    ]

def fetch_page(url):
    """Fetch the HTML content of a page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_school_data(html, location):
    """Parse school data from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    schools = []

    # Try to find schools in the city-specific format first
    city_schools = soup.find_all('div', class_='card-row')

    if city_schools:
        # City-specific page format
        for school_div in city_schools:
            school = {}

            # Get name and URL
            name_elem = school_div.find('h2', class_='card-row-title')
            if name_elem:
                link = name_elem.find('a')
                if link:
                    school['name'] = link.text.strip()
                    href = link.get('href', '')
                    if href.startswith('http'):
                        school['url'] = href
                    else:
                        school['url'] = 'https://www.international-schools-database.com' + href

            # Get description
            desc_elem = school_div.find('div', class_='card-row-content')
            if desc_elem:
                school['description'] = desc_elem.text.strip()

            # Get properties
            props_div = school_div.find('div', class_='card-row-properties')
            if props_div:
                dl = props_div.find('dl')
                if dl:
                    dds = dl.find_all('dd')
                    dts = dl.find_all('dt')
                    for dd, dt in zip(dds, dts):
                        key = dd.text.strip().lower()
                        value = dt.text.strip()
                        if 'curriculum' in key:
                            school['curriculum'] = value
                        elif 'language' in key:
                            school['language'] = value
                        elif 'ages' in key:
                            school['ages'] = value
                        elif 'fees' in key and 'not' not in value.lower():
                            school['fees'] = value

            if school:  # Only append if we found some data
                school['location'] = location
                schools.append(school)

    # If no schools found in city format, try search results format
    if not schools:
        # ... existing search results parsing code ...
        pass

    return schools

def scrape_japanese_schools():
    """Scrape data for all Japanese locations"""
    locations = get_japanese_locations()
    all_schools = []

    for location in locations:
        print(f"Scraping schools in {location['name']}...")
        html = fetch_page(location['url'])

        if html:
            schools = parse_school_data(html, location['name'])
            all_schools.extend(schools)
            print(f"Found {len(schools)} schools in {location['name']}")

            # Be nice to the server
            time.sleep(2)

    return all_schools

def get_school_details(url):
    """Scrape detailed information from a school's page"""
    max_retries = 3
    retry_delay = 5  # seconds

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                verify=True
            )
            response.raise_for_status()
            break  # If successful, break the retry loop
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:  # If not the last attempt
                print(f"Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"All attempts failed for {url}")
                return None

    soup = BeautifulSoup(response.text, 'html.parser')
    details = {}

    # Find the panel group containing all sections
    panel_group = soup.find('div', id='detailed-answers')
    if not panel_group:
        return None

    # Process each panel
    panels = panel_group.find_all('div', class_='panel')
    for panel in panels:
        # Get section name from the heading
        heading = panel.find('div', class_='panel-heading')
        if not heading:
            continue

        section_name = heading.find('i').next_sibling.strip()

        # Get all Q&A pairs from the panel body
        panel_body = panel.find('div', class_='panel-body')
        if not panel_body:
            continue

        qa_pairs = {}
        rows = panel_body.find_all('tr')
        for row in rows:
            question = row.find('td', class_='question')
            answer = row.find('td', class_='answer')
            if question and answer:
                qa_pairs[question.text.strip()] = answer.text.strip()

        details[section_name] = qa_pairs

    return details

def update_schools_with_details():
    """Update the JSON file with detailed information for each school"""
    # Read existing JSON file
    with open('japanese_schools_output.json', 'r', encoding='utf-8') as f:
        schools = json.load(f)

    # Count how many schools need to be scraped
    remaining_schools = sum(1 for school in schools
                          if 'url' in school and ('details' not in school or not school['details']))
    print(f"\nFound {remaining_schools} schools that still need details")

    # Add details for each school
    for i, school in enumerate(schools):
        if 'url' in school:
            # Skip if already has details
            if 'details' in school and school['details']:
                print(f"Skipping {school['name']} - already has details")
                continue

            print(f"\nFetching details for: {school['name']}")
            print(f"Progress: {i+1}/{len(schools)} (Remaining: {remaining_schools})")
            details = get_school_details(school['url'])
            if details:
                school['details'] = details
                remaining_schools -= 1
                print("Successfully fetched details!")
            else:
                print("Failed to fetch details")

            # Longer delay between requests (10-15 seconds)
            delay = 12
            print(f"Waiting {delay} seconds before next request...")
            time.sleep(delay)

        # Save progress more frequently (every 3 schools)
        if (i + 1) % 3 == 0:
            print("\nSaving progress...")
            with open('japanese_schools_output.json', 'w', encoding='utf-8') as f:
                json.dump(schools, f, ensure_ascii=False, indent=2)

    # Final save
    print("\nSaving final results...")
    with open('japanese_schools_output.json', 'w', encoding='utf-8') as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)
    print("Done!")

def main():
    schools = scrape_japanese_schools()

    # Save to JSON file
    output_file = 'japanese_schools_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(schools)} schools total. Data saved to {output_file}")

    print("Starting to update schools with detailed information...")
    update_schools_with_details()
    print("Finished updating schools!")

if __name__ == "__main__":
    main()
