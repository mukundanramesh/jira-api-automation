

import requests
import json
import csv
import pandas as pd  # Used for displaying data in a structured way (optional, but good for preview)

# --- Configuration ---
# Jira Cloud API details
# Your JIRA domain
JIRA_BASE_URL = 'https://appian-eng.atlassian.net'
# Your email associated with the JIRA account
JIRA_API_EMAIL = 'mukundan.ramesh@appian.com'
# --- Security: Get API Token from Environment Variable ---
# Ensure you have set the JIRA_API_TOKEN environment variable
JIRA_API_TOKEN = "ATATT3xFfGF0VpGXq0heJTYq4ag1QJ9TVkANUNm8V1sU0GZ2E-2uCuRmC64bRejMiwHgyv0d2gAd0WjxLt4183ny3jpOff9ctOveDG0y94oR6YClDB6jv5JC0V5vZ7iqvdx17nNWZ2mxAblnmgmWyH0raY2VgsoUeuxdbhcaBN1eD3yphvTdr2Q=8852148D"



# CSV File details
CSV_FILE_PATH = "jira_filters.csv"  # Path to your CSV file
CSV_DELIMITER = ";"  # Delimiter used in your CSV file


# --- Prerequisites Checklist ---
# 1. Jira API Token:
#    - Go to https://id.atlassian.com/manage-profile/security/api-tokens
#    - Create a new API token and copy it.
#    - Replace 'YOUR_JIRA_API_TOKEN' above.

# 2. CSV File Structure:
#    - Create a CSV file (e.g., 'jira_filters.csv' as defined by CSV_FILE_PATH).
#    - Ensure it uses the specified delimiter (';' in this case).
#    - The first row of this CSV file MUST contain these exact column headers:
#      - `Filter Name`: (Required) The name of your Jira filter.
#      - `JQL`: (Required) The JQL query for the filter.
#
#    Note: All filters created by this script will be:
#      - Shared with 'authenticated' users (all logged-in Jira users).
#      - Set as 'Favourite' to FALSE.
#      - Will not have a 'Description'.

# --- Functions ---

def get_csv_data(file_path, delimiter):
    """
    Reads data from a CSV file with the specified delimiter.
    Returns a pandas DataFrame.
    """
    try:
        df = pd.read_csv(file_path, sep=delimiter)
        print(f"Successfully read {len(df)} rows from CSV file '{file_path}'.")
        return df
    except FileNotFoundError:
        print(f"Error: CSV file not found at '{file_path}'.")
        return None
    except Exception as e:
        print(f"Error reading from CSV file: {e}")
        return None


def get_jira_auth_header(email, api_token):
    """
    Returns the Basic Authentication header for Jira API requests.
    """
    import base64
    auth_string = f"{email}:{api_token}"
    encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded_auth_string}"}


def create_jira_filter(base_url, headers, filter_data):
    """
    Creates a new filter in Jira Cloud.
    """
    url = f"{base_url}/rest/api/3/filter"
    headers["Content-Type"] = "application/json"

    print(f"\nAttempting to create filter: '{filter_data.get('name')}'...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(filter_data))
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        created_filter = response.json()
        print(f"Successfully created filter '{created_filter.get('name')}' (ID: {created_filter.get('id')})")
        print(f"View URL: {created_filter.get('viewUrl')}")
        return created_filter
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error creating filter: {errh}")
        print(f"Response Status Code: {response.status_code}")
        try:
            print(f"Response Body: {response.json()}")
        except json.JSONDecodeError:
            print(f"Response Body (text): {response.text}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")
    return None


def main():
    """
    Main function to orchestrate reading from CSV and creating Jira filters.
    """
    print("--- Starting Jira Filter Creation Process ---")

    # 1. Get data from CSV file
    filter_df = get_csv_data(CSV_FILE_PATH, CSV_DELIMITER)

    if filter_df is None or filter_df.empty:
        print("No filter data found or error reading CSV. Exiting.")
        return

    print("\n--- Filter Data from CSV File ---")
    print(filter_df.to_markdown(index=False))  # Display the DataFrame nicely

    # 2. Prepare Jira Authentication Header
    jira_headers = get_jira_auth_header(JIRA_API_EMAIL, JIRA_API_TOKEN)
    if not jira_headers:
        print("Failed to prepare Jira authentication. Exiting.")
        return

    # 3. Process each row and create filter
    filters_created_count = 0
    # Hardcode share permission to 'authenticated'
    authenticated_share_permission = [{"type": "authenticated"}]
    # Hardcode favourite to FALSE
    favourite_status = False
    # Hardcode description to an empty string (or remove if API allows null)
    description_value = ""

    for index, row in filter_df.iterrows():
        filter_name = row.get("Filter Name")
        jql = row.get("JQL")

        if not filter_name or not jql:
            print(f"\nSkipping row {index + 2}: 'Filter Name' or 'JQL' is missing.")
            continue

        filter_payload = {
            "name": filter_name,
            "description": description_value,  # Hardcoded empty description
            "jql": jql,
            "favourite": favourite_status,  # Hardcoded favourite to FALSE
            "sharePermissions": authenticated_share_permission  # Always share with authenticated users
        }

        # Call Jira API to create the filter
        created_filter = create_jira_filter(JIRA_BASE_URL, jira_headers, filter_payload)
        if created_filter:
            filters_created_count += 1

    print(f"\n--- Process Complete ---")
    print(f"Total filters processed from sheet: {len(filter_df)}")
    print(f"Total filters successfully created in Jira: {filters_created_count}")


if __name__ == "__main__":
    main()
