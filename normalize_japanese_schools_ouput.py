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
    Given a list of raw pages, group them by the prefix in their 'site_id' and merge data.
    Returns a dict: { 'site_id': {...aggregated...}, ... }
    """
    aggregated = {}
    current_id = 1  # Start IDs at 1

    for page in raw_pages:
        # Generate site_id from URL (last part of the URL path)
        url = page.get("url", "")
        site_id = url.split("/")[-1] if url else None

        if not site_id:
            print(f"[!] Skipping entry with no URL: {page.get('name', 'Unknown')}")
            continue

        print(f"[+] Processing school: {page.get('name', 'Unknown')} (site_id: {site_id})")

        if site_id not in aggregated:
            # Initialize an empty structure for this site_id
            aggregated[site_id] = {
                "school_id": current_id,  # Use sequential ID instead of 0
                "site_id": site_id,
                "name_en": "",
                "name_jp": "",
                "location_en": "",
                "location_jp": "",
                "phone_en": "",
                "phone_jp": "",
                "email_en": "",
                "email_jp": "",
                "address_en": "",
                "address_jp": "",
                "curriculum_en": "",
                "curriculum_jp": "",
                "structured_data": {},
                "url_en": page.get("url_en", ""),
                "url_jp": page.get("url_jp", ""),
                "logo_id": "",
                "image_id": "",
                "affiliations_en": [],
                "affiliations_jp": [],
                "accreditation_en": [],
                "accreditation_jp": [],
                "education_programs_offered_en": [],
                "education_programs_offered_jp": [],
                "education_curriculum_en": "",
                "education_curriculum_jp": "",
                "education_academic_support_en": [],
                "education_academic_support_jp": [],
                "education_extracurricular_activities_en": [],
                "education_extracurricular_activities_jp": [],
                "admissions_acceptance_policy_en": "",
                "admissions_acceptance_policy_jp": "",
                "admissions_application_guidelines_en": "",
                "admissions_application_guidelines_jp": "",
                "admissions_age_requirements_en": "",
                "admissions_age_requirements_jp": "",
                "admissions_fees_en": "",
                "admissions_fees_jp": "",
                # Add all other fields as per the schema with default values
                "events_en": [],
                "events_jp": [],
                "campus_facilities_en": [],
                "campus_facilities_jp": [],
                "campus_virtual_tour_en": "",
                "campus_virtual_tour_jp": "",
                "student_life_counseling_en": "",
                "student_life_counseling_jp": "",
                "student_life_support_services_en": [],
                "student_life_support_services_jp": [],
                "student_life_library_en": "",
                "student_life_library_jp": "",
                "student_life_calendar_en": "",
                "student_life_calendar_jp": "",
                "student_life_tour_en": "",
                "student_life_tour_jp": "",
                "employment_open_positions_en": [],
                "employment_open_positions_jp": [],
                "employment_application_process_en": "",
                "employment_application_process_jp": "",
                "policies_privacy_policy_en": "",
                "policies_privacy_policy_jp": "",
                "policies_terms_of_use_en": "",
                "policies_terms_of_use_jp": "",
                "staff_staff_list_en": [],
                "staff_staff_list_jp": [],
                "staff_board_members_en": [],
                "staff_board_members_jp": [],
                "short_description_en": "",
                "short_description_jp": "",
                "description_en": "",
                "description_jp": "",
                "country_en": "",
                "country_jp": "",
                "region_en": "",
                "region_jp": "",
                "geography_en": "",
                "geography_jp": ""
            }
            current_id += 1  # Increment ID for next school

        site_obj = aggregated[site_id]

        # Map English and Japanese fields
        site_obj["name_jp"] = page.get("name", "")
        site_obj["description_jp"] = page.get("description", "")
        site_obj["curriculum_jp"] = page.get("curriculum", "")
        site_obj["language_jp"] = page.get("language", "")
        site_obj["ages_jp"] = page.get("ages", "")
        site_obj["fees_jp"] = page.get("fees", "")
        site_obj["location_jp"] = page.get("location", "")
        site_obj["url_jp"] = page.get("url", "")

        # Assuming English fields are available similarly
        site_obj["name_en"] = page.get("name_en", "")
        site_obj["description_en"] = page.get("description_en", "")
        site_obj["curriculum_en"] = page.get("curriculum_en", "")
        site_obj["language_en"] = page.get("language_en", "")
        site_obj["ages_en"] = page.get("ages_en", "")
        site_obj["fees_en"] = page.get("fees_en", "")
        site_obj["location_en"] = page.get("location_en", "")
        site_obj["url_en"] = page.get("url_en", "")

        # Populate structured_data if available
        structured_data = page.get("details", {})
        site_obj["structured_data"] = structured_data

        # Add sub-pages
        page_title = page.get("title", "Untitled")
        page_data = page.get("data", "")
        add_sub_page(site_obj, page_title, page_data)

        # Add staff members if available
        staff = page.get("staff", [])
        for member in staff:
            add_staff_member(site_obj, member.get("name", ""), member.get("role", ""))

    return aggregated

def main():
    en_file = "japanese_schools_output.json"
    jp_file = "japanese_schools_output_jp.json"
    output_file = "normalized_japanese_schools.json"

    # Check if input files exist
    if not os.path.exists(en_file) or not os.path.exists(jp_file):
        print(f"[!] Input files not found.")
        return

    # Load both files
    print(f"[+] Reading {en_file} and {jp_file}...")
    with open(en_file, "r", encoding="utf-8") as f:
        en_pages = json.load(f)
    with open(jp_file, "r", encoding="utf-8") as f:
        jp_pages = json.load(f)

    # Combine the pages
    raw_pages = en_pages + jp_pages
    print(f"[+] Loaded {len(raw_pages)} raw pages ({len(en_pages)} English, {len(jp_pages)} Japanese)")

    # 1. Aggregate by site_id
    print("[+] Aggregating pages...")
    aggregated = aggregate_pages(raw_pages)
    print(f"[+] Aggregated into {len(aggregated)} unique schools")

    # 2. Convert to a list for final output
    normalized_list = list(aggregated.values())

    # 3. Write out the final JSON
    print(f"[+] Writing {len(normalized_list)} schools to {output_file}")
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(normalized_list, out, ensure_ascii=False, indent=2)

    print(f"[+] Aggregation complete. See {output_file}")

if __name__ == "__main__":
    main()
