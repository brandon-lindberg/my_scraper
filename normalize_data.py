import json
import os
import re
import string

def is_clean_text(data, max_invalid_ratio=0.1):
    """
    Check if the provided data contains primarily valid characters.
    Allows printable ASCII and Japanese characters (Hiragana, Katakana, Kanji).
    Returns True if the ratio of invalid characters is below the max_invalid_ratio.

    Parameters:
    - data (str): The text data to validate.
    - max_invalid_ratio (float): Maximum allowed ratio of invalid characters.
    """
    if not data:
        return False

    valid_char_pattern = re.compile(
        r'['
        r'\u3040-\u309F'  # Hiragana
        r'\u30A0-\u30FF'  # Katakana
        r'\u4E00-\u9FFF'  # Kanji
        r'\uFF00-\uFFEF'  # Half-width and Full-width Forms
        r' -~'             # Printable ASCII
        r'\n\r\t'          # Common whitespace characters
        r']'
    )

    total_chars = len(data)
    if total_chars == 0:
        return False

    valid_chars = len(valid_char_pattern.findall(data))
    invalid_chars = total_chars - valid_chars

    invalid_ratio = invalid_chars / total_chars
    return invalid_ratio <= max_invalid_ratio

def add_sub_page(site_obj, page_title, page_data):
    """
    Add a sub-page entry to site_obj["content"]["sub_pages"],
    skipping duplicates and data with excessive invalid characters.
    """
    if not page_data.strip():
        return  # Skip empty data

    if not is_clean_text(page_data):
        return  # Skip data with excessive strange characters

    # Check for exact duplicate data
    for sp in site_obj["content"]["sub_pages"]:
        if sp["data"] == page_data:
            # Already have this exact text stored
            return

    site_obj["content"]["sub_pages"].append({
        "title": page_title,
        "data": page_data
    })

def add_staff_member(site_obj, name, role):
    """
    Add a staff member with their role to site_obj["content"]["structured_data"]["staff"]["staff_list"],
    skipping duplicates.
    """
    if not name.strip() or not role.strip():
        return  # Skip if name or role is empty

    # Check for exact duplicate entry
    for staff in site_obj["content"]["structured_data"]["staff"]["staff_list"]:
        if staff["name"] == name and staff["role"] == role:
            return  # Duplicate found

    site_obj["content"]["structured_data"]["staff"]["staff_list"].append({
        "name": name,
        "role": role
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
                            "procedure": "",
                            "language_requirements_students": "",
                            "language_requirements_parents": ""
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
                        },
                        "staff": {
                            "staff_list": [],
                            "board_members": []
                        }

                    }
                },
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

        # Create a new sub-page entry for the current page
        # Title is now directly from page title without headers
        page_title = page.get("title", "Untitled")
        page_data = page.get("data", "")
        add_sub_page(site_obj, page_title, page_data)

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
