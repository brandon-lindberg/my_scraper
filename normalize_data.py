import json
import os
import re

def merge_headers(existing_headers, new_headers):
    """
    Merge new headers into existing_headers, removing duplicates.
    existing_headers/new_headers look like:
        {
          "h1": [...],
          "h2": [...],
          "h3": [...]
        }
    """
    for level in ["h1", "h2", "h3"]:
        old_list = existing_headers.get(level, [])
        new_list = new_headers.get(level, [])
        merged = set(old_list) | set(new_list)  # union to remove duplicates
        existing_headers[level] = list(merged)
    return existing_headers

def get_page_title_from_headers(page_headers, fallback_title):
    """
    Returns the first non-empty header from h1, h2, or h3.
    If none exist, returns fallback_title (e.g., the <title> or "Untitled").
    """
    h1 = page_headers.get("h1", [])
    h2 = page_headers.get("h2", [])
    h3 = page_headers.get("h3", [])

    # Ensure they are lists, not strings
    if isinstance(h1, str):
        h1 = [h1]
    if isinstance(h2, str):
        h2 = [h2]
    if isinstance(h3, str):
        h3 = [h3]

    if len(h1) > 0 and h1[0].strip():
        return h1[0]
    elif len(h2) > 0 and h2[0].strip():
        return h2[0]
    elif len(h3) > 0 and h3[0].strip():
        return h3[0]
    else:
        return fallback_title if fallback_title else "Untitled"

def add_sub_page(site_obj, page_title, page_data):
    """
    Add a sub-page entry to site_obj["content"]["sub_pages"],
    skipping duplicates if needed.
    """
    if not page_data.strip():
        return  # skip empty data

    # Check for exact duplicate data
    for sp in site_obj["content"]["sub_pages"]:
        if sp["data"] == page_data:
            # Already have this exact text stored
            return

    site_obj["content"]["sub_pages"].append({
        "title": page_title,
        "data": page_data
    })

def aggregate_pages(raw_pages):
    """
    Given a list of raw pages (with IDs like '1-1', '1-2', '2-1'),
    group them by the prefix in their 'id' and merge data.
    Returns a dict: { '1': {...aggregated...}, '2': {...aggregated...}, ... }
    """
    aggregated = {}

    for page in raw_pages:
        # Example: if page["id"] = "1-2", site_id = "1"
        page_id = page.get("id", "")
        site_id = page_id.split("-")[0] if "-" in page_id else page_id

        if site_id not in aggregated:
            # Initialize an empty structure for this site_id
            aggregated[site_id] = {
                "source": {
                    "id": site_id,
                    "url": page.get("url", ""),
                    "title": page.get("title", ""),
                    "scrapedAt": page.get("scrapedAt", "")
                },
                "content": {
                    "headers": {
                        "h1": [],
                        "h2": [],
                        "h3": []
                    },
                    # Instead of one big "main_text", keep each page's data separately
                    "sub_pages": [],
                    "structured_data": {
                        "school_info": {
                            "name": "",
                            "location": "",
                            "contact": {
                                "phone": "",
                                "email": "",
                                "address": ""
                            },
                            "affiliations": [],
                            "accreditation": []
                        },
                        "education": {
                            "programs_offered": [],
                            "curriculum": "",
                            "academic_support": [],
                            "extracurricular_activities": []
                        },
                        "admissions": {
                            "acceptance_policy": "",
                            "application_guidelines": "",
                            "age_requirements": "",
                            "fees": "",
                            "breakdown_fees": {
                              "application_fee": "",
                              "day_care_fee": {
                                "tuition": "",  
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "kindergarten": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "grade_elementary": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "grade_junior_high": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "grade_high_school": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "summer_school": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              },
                              "other": {
                                "tuition": "",
                                "registration_fee": "",
                                "maintenance_fee": ""
                              }
                            },
                            "procedure": ""
                        },
                        "events": [],
                        "campus": {
                            "facilities": [],
                            "virtual_tour": ""
                        },
                        "student_life": {
                            "counseling": "",
                            "support_services": [],
                            "library": "",
                            "calendar": "",
                            "tour": ""
                        },
                        "employment": {
                            "open_positions": [],
                            "application_process": ""
                        },
                        "policies": {
                            "privacy_policy": "",
                            "terms_of_use": ""
                        }
                    }
                },
                "links": []
            }
        site_obj = aggregated[site_id]

        # Merge 'source' fields
        # We'll choose to keep the earliest "scrapedAt" as the official one
        current_scraped_at = page.get("scrapedAt", "")
        existing_scraped_at = site_obj["source"].get("scrapedAt", "")

        if current_scraped_at and (not existing_scraped_at or current_scraped_at < existing_scraped_at):
            site_obj["source"]["url"] = page.get("url", "")
            site_obj["source"]["title"] = page.get("title", "")
            site_obj["source"]["scrapedAt"] = current_scraped_at

        # Merge top-level headers across the site
        existing_headers = site_obj["content"]["headers"]
        new_headers = page.get("headers", {})
        site_obj["content"]["headers"] = merge_headers(existing_headers, new_headers)

        # Create a new sub-page entry for the current page
        # Title: first non-empty h1/h2/h3 or fallback to <title>
        page_title = get_page_title_from_headers(new_headers, fallback_title=page.get("title"))
        page_data = page.get("data", "")
        add_sub_page(site_obj, page_title, page_data)

        # Merge links (deduplicate via set)
        existing_links = set(site_obj["links"])
        new_links = set(page.get("links", []))
        merged_links = existing_links.union(new_links)
        site_obj["links"] = list(merged_links)

    return aggregated

def main():
    input_file = "scraped_output.json"
    output_file = "normalized_output.json"

    if not os.path.exists(input_file):
        print(f"[!] {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        raw_pages = json.load(f)

    # 1. Aggregate by site_id
    aggregated = aggregate_pages(raw_pages)

    # 2. Convert to a list for final output
    normalized_list = list(aggregated.values())

    # 3. Write out the final JSON
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(normalized_list, out, ensure_ascii=False, indent=2)

    print(f"[+] Aggregation complete. See {output_file}")

if __name__ == "__main__":
    main()
