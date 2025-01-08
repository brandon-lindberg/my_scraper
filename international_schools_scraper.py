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
                    school['url'] = 'https://www.international-schools-database.com' + link.get('href', '')

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

def main():
    schools = scrape_japanese_schools()

    # Save to JSON file
    output_file = 'japanese_schools_output.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schools, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(schools)} schools total. Data saved to {output_file}")

if __name__ == "__main__":
    main()
